-- AiX Decision System Database Schema
-- MySQL 8.0+

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user' NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Papers table
CREATE TABLE IF NOT EXISTS papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    status ENUM('uploaded', 'extracted', 'failed') DEFAULT 'uploaded' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paper extractions table
CREATE TABLE IF NOT EXISTS paper_extractions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paper_id INT NOT NULL,
    raw_text LONGTEXT,
    schema_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Datasets table (stage=DRAFT|PREVIEW|COMMITTED; committed=1 allows pipeline run-step)
CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    row_count INT,
    column_count INT,
    schema_json TEXT,
    stage VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    committed TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed catalog table
CREATE TABLE IF NOT EXISTS seed_catalog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    process_type VARCHAR(50) NOT NULL,
    seed_path VARCHAR(500) NOT NULL,
    schema_json TEXT,
    source_type ENUM('paper', 'dataset', 'synthetic') NOT NULL,
    source_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_process_type (process_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Synthetic runs table
CREATE TABLE IF NOT EXISTS synthetic_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    process_type VARCHAR(50) NOT NULL,
    template VARCHAR(100),
    config_json TEXT,
    output_seed_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========== System Settings (guardrails, thresholds, integrations) ==========
-- Process window: one row per variable (key = variable name)
CREATE TABLE IF NOT EXISTS process_window (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `key` VARCHAR(128) NOT NULL UNIQUE,
    unit VARCHAR(64),
    hard_min DOUBLE NOT NULL,
    hard_max DOUBLE NOT NULL,
    note VARCHAR(512),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Alarm thresholds: single row (id=1)
CREATE TABLE IF NOT EXISTS alarm_thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    enable_weco TINYINT(1) NOT NULL DEFAULT 1,
    sigma_threshold DOUBLE NOT NULL DEFAULT 3.0,
    ewma_lambda DOUBLE NOT NULL DEFAULT 0.2,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Integrations: one row per type (database, streaming, storage, notifications)
CREATE TABLE IF NOT EXISTS integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(64) NOT NULL UNIQUE,
    config_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed default process window rows (run once or via app)
INSERT IGNORE INTO process_window (`key`, unit, hard_min, hard_max, note) VALUES
('pressure_torr', 'Torr', 20.0, 60.0, 'Chamber pressure window'),
('bias_power_w', 'W', 0.0, 500.0, 'RF bias power safety range'),
('chuck_temp_c', '°C', 10.0, 80.0, NULL),
('temperature', '°C', 840.0, 860.0, 'Process temperature range');

-- Seed single alarm_thresholds row
INSERT IGNORE INTO alarm_thresholds (id, enable_weco, sigma_threshold, ewma_lambda) VALUES (1, 1, 3.0, 0.2);

-- Seed integration types (config_json can be null until configured)
INSERT IGNORE INTO integrations (type, config_json) VALUES
('database', NULL),
('streaming', NULL),
('storage', NULL),
('notifications', NULL);

-- Insert default admin user (password: admin123)
-- NOTE: This is a placeholder hash. In production, use a proper bcrypt hash.
-- To generate: python -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('admin123'))"
-- For now, you can create admin user via signup endpoint or manually with proper hash

-- ========== VPD Process Window ==========
CREATE TABLE IF NOT EXISTS vpd_grids (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grid_id VARCHAR(64) NOT NULL UNIQUE,
    temp_min DOUBLE NOT NULL,
    temp_max DOUBLE NOT NULL,
    temp_step DOUBLE NOT NULL,
    rh_min DOUBLE NOT NULL,
    rh_max DOUBLE NOT NULL,
    rh_step DOUBLE NOT NULL,
    temps_json TEXT NOT NULL,
    rhs_json TEXT NOT NULL,
    vpd_matrix_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_grid_id (grid_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vpd_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_min_kpa DOUBLE NOT NULL,
    target_max_kpa DOUBLE NOT NULL,
    temp_constraint_min DOUBLE,
    temp_constraint_max DOUBLE,
    rh_constraint_min DOUBLE,
    rh_constraint_max DOUBLE,
    metric_key VARCHAR(64) DEFAULT 'defect_rate',
    recommend_mode VARCHAR(32) DEFAULT 'simple',
    created_by_user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_created_by (created_by_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS doe_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL UNIQUE,
    tool_id VARCHAR(64),
    recipe_id VARCHAR(64),
    batch_id VARCHAR(64),
    started_at DATETIME,
    ended_at DATETIME,
    factors_json TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_run_id (run_id),
    INDEX idx_started_at (started_at),
    INDEX idx_tool_recipe_batch (tool_id, recipe_id, batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS doe_measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    metric_key VARCHAR(64) NOT NULL,
    metric_value DOUBLE NOT NULL,
    unit VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES doe_runs(id) ON DELETE CASCADE,
    INDEX idx_run_metric (run_id, metric_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
