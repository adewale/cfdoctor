# container-idle-window

Known-bad fixture for `CFDOC-COST-CONTAINER-IDLE-WINDOW`.

A Worker routes `/transcode` requests to an FFmpeg Container. The workload is
genuinely container-shaped — a native binary that cannot run in a Worker
isolate — so the primitive choice is not the defect.

The defect is the idle window. `TranscodeContainer` declares no `sleepAfter`
and does not override `onActivityExpired()`, so after the last request the
instance stays awake for the platform default before charges stop. Containers
bill memory and disk on the instance's *provisioned* size for every 10ms the
instance is awake, and this one is `standard-4` (the largest instance type).
Bursty, spread-out transcodes therefore pay a full-size idle tail once per
wake, on top of the transcode itself.

The scanner suppresses this lead when the project sets `sleepAfter` anywhere,
or when it manages the timer explicitly via `onActivityExpired()` /
`renewActivityTimeout()`, because either is evidence the idle window was a
decision rather than an unexamined default.

Two independent production write-ups motivated the check: VideoToBe's FFmpeg
transcoder and Kent C. Dodds' podcast pipeline both had to actively manage
container wake/sleep behaviour after shipping — Kent explicitly added idle
signalling "instead of relying on timeout windows."
