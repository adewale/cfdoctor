CREATE TABLE hcpcs_codes (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL,
  description TEXT NOT NULL
);

CREATE TABLE states (
  id INTEGER PRIMARY KEY,
  abbreviation TEXT NOT NULL,
  name TEXT NOT NULL
);

-- Hundreds of thousands of rows and growing: one row per (year, state, procedure).
-- No secondary indexes anywhere: every filtered or aggregate query scans the table.
CREATE TABLE reimbursement (
  id INTEGER PRIMARY KEY,
  year INTEGER NOT NULL,
  state_id INTEGER NOT NULL,
  hcpcs_code_id INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL
);
