# Per-consumer Queue matching

The repository config declares a safe consumer for one queue, while the shared handler explicitly branches on a second queue whose retry/DLQ configuration is absent.
