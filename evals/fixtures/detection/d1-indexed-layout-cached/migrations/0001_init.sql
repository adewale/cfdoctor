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

CREATE TABLE reimbursement (
  id INTEGER PRIMARY KEY,
  year INTEGER NOT NULL,
  state_id INTEGER NOT NULL,
  hcpcs_code_id INTEGER NOT NULL,
  amount_cents INTEGER NOT NULL
);
