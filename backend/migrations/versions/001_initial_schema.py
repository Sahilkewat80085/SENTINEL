"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-06-06 20:30:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. repositories table
    op.create_table(
        'repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('default_branch', sa.String(length=128), server_default='main', nullable=True),
        sa.Column('folders', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('jira_patterns', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('sync_mode', sa.String(length=20), server_default='api', nullable=True),
        sa.Column('sync_interval', sa.Integer(), server_default='30', nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_sha', sa.String(length=40), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. authors table
    op.create_table(
        'authors',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('github_username', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 3. commits table
    op.create_table(
        'commits',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('sha', sa.String(length=40), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch', sa.String(length=255), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('commit_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha', 'repository_id', name='uq_commits_sha_repository')
    )
    op.create_index('idx_commits_sha', 'commits', ['sha'], unique=False)
    op.create_index('idx_commits_date', 'commits', ['commit_date'], unique=False)
    op.create_index('idx_commits_repo', 'commits', ['repository_id'], unique=False)
    op.create_index('idx_commits_author', 'commits', ['author_id'], unique=False)

    # 4. commit_files table
    op.create_table(
        'commit_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('commit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('folder', sa.String(length=255), nullable=True),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('additions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('deletions', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['commit_id'], ['commits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('commit_id', 'file_path', name='uq_commit_files_commit_path')
    )
    op.create_index('idx_commit_files_folder', 'commit_files', ['folder'], unique=False)
    op.create_index('idx_commit_files_path', 'commit_files', ['file_path'], unique=False)

    # 5. commit_jiras table
    op.create_table(
        'commit_jiras',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('commit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('jira_id', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['commit_id'], ['commits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('commit_id', 'jira_id', name='uq_commit_jiras_commit_jira')
    )
    op.create_index('idx_commit_jiras_jira', 'commit_jiras', ['jira_id'], unique=False)

    # 6. file_hashes table
    op.create_table(
        'file_hashes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('folder', sa.String(length=255), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('last_commit_sha', sa.String(length=40), nullable=False),
        sa.Column('last_commit_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'file_path', 'folder', name='uq_file_hashes_repo_path_folder')
    )
    op.create_index('idx_file_hashes_path', 'file_hashes', ['file_path'], unique=False)
    op.create_index('idx_file_hashes_folder', 'file_hashes', ['folder'], unique=False)
    op.create_index('idx_file_hashes_hash', 'file_hashes', ['sha256_hash'], unique=False)

    # 7. governance_snapshots table
    op.create_table(
        'governance_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('total_jiras', sa.Integer(), nullable=False),
        sa.Column('total_commits', sa.Integer(), nullable=False),
        sa.Column('overall_coverage_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('missing_merge_count', sa.Integer(), nullable=True),
        sa.Column('critical_violation_count', sa.Integer(), nullable=True),
        sa.Column('avg_delay_days', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('governance_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'snapshot_date', name='uq_gov_snapshots_repo_date')
    )

    # 8. folder_health_snapshots table
    op.create_table(
        'folder_health_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('folder_name', sa.String(length=255), nullable=False),
        sa.Column('health_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('coverage_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('consistency_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('timeliness_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('completeness_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'snapshot_date', 'folder_name', name='uq_folder_snapshots_repo_date_folder')
    )

    # 9. rule_violations table
    op.create_table(
        'rule_violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', sa.String(length=20), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('jira_id', sa.String(length=50), nullable=True),
        sa.Column('folder_name', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=1024), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('acknowledged_by', sa.String(length=255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledge_note', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'rule_id', 'jira_id', 'folder_name', 'file_path', name='uq_rule_violations_fields')
    )
    op.create_index('idx_violations_severity', 'rule_violations', ['severity'], unique=False)
    op.create_index('idx_violations_rule', 'rule_violations', ['rule_id'], unique=False)
    op.create_index('idx_violations_jira', 'rule_violations', ['jira_id'], unique=False)

    # 10. reports table
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_type', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('generated_by', sa.String(length=255), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=512), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='viewer', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'], unique=True)
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # 12. audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_log_user', 'audit_log', ['user_id'], unique=False)
    op.create_index('idx_audit_log_action', 'audit_log', ['action'], unique=False)
    op.create_index('idx_audit_log_date', 'audit_log', ['created_at'], unique=False)

    # 13. materialized views and their unique indexes
    op.execute(
        """
        CREATE MATERIALIZED VIEW mv_jira_summary AS
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
        """
    )
    op.execute("CREATE UNIQUE INDEX idx_mv_jira_summary ON mv_jira_summary(jira_id, repository_id);")

    op.execute(
        """
        CREATE MATERIALIZED VIEW mv_coverage_matrix AS
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
        """
    )
    op.execute("CREATE UNIQUE INDEX idx_mv_coverage ON mv_coverage_matrix(jira_id, repository_id, expected_folder);")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_coverage_matrix;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_jira_summary;")

    op.drop_table('audit_log')
    op.drop_table('users')
    op.drop_table('reports')
    op.drop_table('rule_violations')
    op.drop_table('folder_health_snapshots')
    op.drop_table('governance_snapshots')
    op.drop_table('file_hashes')
    op.drop_table('commit_jiras')
    op.drop_table('commit_files')
    op.drop_table('commits')
    op.drop_table('authors')
    op.drop_table('repositories')
