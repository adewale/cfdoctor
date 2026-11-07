CREATE TABLE post_reads (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL,
  client_id TEXT NOT NULL,
  read_ms INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
