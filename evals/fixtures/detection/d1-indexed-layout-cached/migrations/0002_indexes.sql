-- Composite indexes matching the hot query predicates. After applying a batch
-- of index changes, run ANALYZE (or PRAGMA optimize) once so sqlite_stat1
-- statistics exist and the query planner actually chooses these indexes.
CREATE INDEX reimbursement_year_idx ON reimbursement(year);
CREATE INDEX reimbursement_year_hcpcs_idx ON reimbursement(year, hcpcs_code_id);
CREATE INDEX reimbursement_year_state_idx ON reimbursement(year, state_id);
CREATE INDEX reimbursement_state_hcpcs_idx ON reimbursement(state_id, hcpcs_code_id);

CREATE UNIQUE INDEX hcpcs_codes_code_idx ON hcpcs_codes(code);
CREATE UNIQUE INDEX states_abbreviation_idx ON states(abbreviation);
