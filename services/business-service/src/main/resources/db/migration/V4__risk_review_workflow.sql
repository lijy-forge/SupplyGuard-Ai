ALTER TABLE supplier_risk_metrics ADD COLUMN observed_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE TABLE supplier_risk_reviews (
  id VARCHAR(36) PRIMARY KEY,
  request_key VARCHAR(80) NOT NULL UNIQUE,
  case_number VARCHAR(80) NOT NULL,
  part_number VARCHAR(80) NOT NULL,
  current_supplier VARCHAR(50) NOT NULL,
  snapshot TEXT NOT NULL,
  status VARCHAR(30) NOT NULL,
  record_version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP(6) NOT NULL,
  reviewed_at TIMESTAMP(6),
  decision TEXT,
  action_id VARCHAR(36)
);
