-- ============================================================
-- SENTINEL — Raw Schema Initialization Script
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- CORE TABLES
CREATE TABLE IF NOT EXISTS repositories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL UNIQUE,
    url             VARCHAR(512) NOT NULL,
    default_branch  VARCHAR(128) DEFAULT 'main',
    folders         JSONB NOT NULL DEFAULT '[]',
    jira_patterns   JSONB NOT NULL DEFAULT '[]',
    sync_mode       VARCHAR(20) DEFAULT 'api',
    sync_interval   INTEGER DEFAULT 30,
    last_synced_at  TIMESTAMPTZ,
    last_sync_sha   VARCHAR(40),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS authors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    github_username VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS commits (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sha             VARCHAR(40) NOT NULL,
    repository_id   UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    author_id       UUID NOT NULL REFERENCES authors(id) ON DELETE RESTRICT,
    branch          VARCHAR(255),
    message         TEXT NOT NULL,
    commit_date     TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(sha, repository_id)
);

CREATE INDEX IF NOT EXISTS idx_commits_sha ON commits(sha);
CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(commit_date);
CREATE INDEX IF NOT EXISTS idx_commits_repo ON commits(repository_id);
CREATE INDEX IF NOT EXISTS idx_commits_author ON commits(author_id);

CREATE TABLE IF NOT EXISTS commit_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id       UUID NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    file_path       VARCHAR(1024) NOT NULL,
    folder          VARCHAR(255),
    change_type     VARCHAR(20) NOT NULL,
    additions       INTEGER DEFAULT 0,
    deletions       INTEGER DEFAULT 0,
    UNIQUE(commit_id, file_path)
);

CREATE INDEX IF NOT EXISTS idx_commit_files_folder ON commit_files(folder);
CREATE INDEX IF NOT EXISTS idx_commit_files_path ON commit_files(file_path);

CREATE TABLE IF NOT EXISTS commit_jiras (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id       UUID NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    jira_id         VARCHAR(50) NOT NULL,
    UNIQUE(commit_id, jira_id)
);

CREATE INDEX IF NOT EXISTS idx_commit_jiras_jira ON commit_jiras(jira_id);

-- CONTENT VERIFICATION
CREATE TABLE IF NOT EXISTS file_hashes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path       VARCHAR(1024) NOT NULL,
    folder          VARCHAR(255) NOT NULL,
    sha256_hash     VARCHAR(64) NOT NULL,
    file_size       BIGINT NOT NULL,
    last_commit_sha VARCHAR(40) NOT NULL,
    last_commit_date TIMESTAMPTZ NOT NULL,
    verified_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repository_id, file_path, folder)
);

CREATE INDEX IF NOT EXISTS idx_file_hashes_path ON file_hashes(file_path);
CREATE INDEX IF NOT EXISTS idx_file_hashes_folder ON file_hashes(folder);
CREATE INDEX IF NOT EXISTS idx_file_hashes_hash ON file_hashes(sha256_hash);

-- GOVERNANCE SNAPSHOTS (for trends)
CREATE TABLE IF NOT EXISTS governance_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    snapshot_date       DATE NOT NULL,
    total_jiras         INTEGER NOT NULL,
    total_commits       INTEGER NOT NULL,
    overall_coverage_pct DECIMAL(5,2),
    missing_merge_count INTEGER,
    critical_violation_count INTEGER,
    avg_delay_days      DECIMAL(8,2),
    governance_score    DECIMAL(5,2),
    metadata            JSONB DEFAULT '{}',
    UNIQUE(repository_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS folder_health_snapshots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    snapshot_date       DATE NOT NULL,
    folder_name         VARCHAR(255) NOT NULL,
    health_score        DECIMAL(5,2),
    coverage_score      DECIMAL(5,2),
    consistency_score   DECIMAL(5,2),
    timeliness_score    DECIMAL(5,2),
    completeness_score  DECIMAL(5,2),
    UNIQUE(repository_id, snapshot_date, folder_name)
);

-- EXCEPTION DETECTION
CREATE TABLE IF NOT EXISTS rule_violations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    rule_id             VARCHAR(20) NOT NULL,
    severity            VARCHAR(20) NOT NULL,
    category            VARCHAR(50) NOT NULL,
    jira_id             VARCHAR(50),
    folder_name         VARCHAR(255),
    file_path           VARCHAR(1024),
    description         TEXT NOT NULL,
    details             JSONB DEFAULT '{}',
    is_acknowledged     BOOLEAN DEFAULT false,
    acknowledged_by     VARCHAR(255),
    acknowledged_at     TIMESTAMPTZ,
    acknowledge_note    TEXT,
    detected_at         TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    UNIQUE(repository_id, rule_id, jira_id, folder_name, file_path)
);

CREATE INDEX IF NOT EXISTS idx_violations_severity ON rule_violations(severity);
CREATE INDEX IF NOT EXISTS idx_violations_rule ON rule_violations(rule_id);
CREATE INDEX IF NOT EXISTS idx_violations_jira ON rule_violations(jira_id);

-- REPORTING
CREATE TABLE IF NOT EXISTS reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id       UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    report_type         VARCHAR(20) NOT NULL,
    file_path           VARCHAR(1024) NOT NULL,
    file_size           BIGINT,
    config              JSONB DEFAULT '{}',
    generated_by        VARCHAR(255),
    generated_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ
);

-- USERS & AUDIT
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username            VARCHAR(255) NOT NULL UNIQUE,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(512) NOT NULL,
    role                VARCHAR(20) NOT NULL DEFAULT 'viewer',
    is_active           BOOLEAN DEFAULT true,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    last_login_at       TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    action              VARCHAR(100) NOT NULL,
    entity_type         VARCHAR(50),
    entity_id           VARCHAR(255),
    details             JSONB DEFAULT '{}',
    ip_address          VARCHAR(45),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_date ON audit_log(created_at);

-- MATERIALIZED VIEWS (Performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jira_summary AS
SELECT
    cj.jira_id,
    r.id AS repository_id,
    COUNT(DISTINCT c.sha) AS commit_count,
    COUNT(DISTINCT c.author_id) AS author_count,
    MIN(c.commit_date) AS first_seen,
    MAX(c.commit_date) AS last_updated,
    ARRAY_AGG(DISTINCT cf.folder) FILTER (WHERE cf.folder IS NOT NULL) AS touched_folders,
    COUNT(DISTINCT cf.folder) AS folder_count
FROM commit_jiras cj
JOIN commits c ON c.id = cj.commit_id
JOIN repositories r ON r.id = c.repository_id
LEFT JOIN commit_files cf ON cf.commit_id = c.id
GROUP BY cj.jira_id, r.id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_jira_summary ON mv_jira_summary(jira_id, repository_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_coverage_matrix AS
SELECT
    cj.jira_id,
    r.id AS repository_id,
    f.folder_name AS expected_folder,
    COALESCE(BOOL_OR(cf.folder IS NOT NULL), false) AS is_merged,
    MIN(c.commit_date) FILTER (WHERE cf.folder = f.folder_name) AS merge_date
FROM commit_jiras cj
JOIN commits c ON c.id = cj.commit_id
JOIN repositories r ON r.id = c.repository_id
CROSS JOIN LATERAL jsonb_array_elements_text(r.folders) AS f(folder_name)
LEFT JOIN commit_files cf ON cf.commit_id = c.id AND cf.folder = f.folder_name
GROUP BY cj.jira_id, r.id, f.folder_name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_coverage ON mv_coverage_matrix(jira_id, repository_id, expected_folder);
