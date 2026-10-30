"""add_github_historical_jobs_tables

Revision ID: c10a23e45678
Revises: b89d12e34567
Create Date: 2026-10-30 23:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c10a23e45678'
down_revision: Union[str, Sequence[str], None] = 'b89d12e34567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create github_accounts table
    if 'github_accounts' not in tables:
        op.create_table(
            'github_accounts',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('github_user_id', sa.String(length=100), nullable=True),
            sa.Column('github_username', sa.String(length=255), nullable=False),
            sa.Column('installation_id', sa.String(length=100), nullable=True),
            sa.Column('encrypted_access_token', sa.Text(), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(), nullable=True),
            sa.Column('scopes', sa.String(length=512), server_default=sa.text("'repo,read:user'"), nullable=False),
            sa.Column('account_type', sa.String(length=50), server_default=sa.text("'oauth'"), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_github_accounts_user_id', 'github_accounts', ['user_id'], unique=False)
        op.create_index('ix_github_accounts_id', 'github_accounts', ['id'], unique=False)

    # 2. Create github_webhook_logs table
    if 'github_webhook_logs' not in tables:
        op.create_table(
            'github_webhook_logs',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('delivery_id', sa.String(length=100), nullable=False),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('repository_name', sa.String(length=255), nullable=True),
            sa.Column('sender_username', sa.String(length=255), nullable=True),
            sa.Column('payload_json', sa.Text(), server_default=sa.text("'{}'"), nullable=False),
            sa.Column('status', sa.String(length=50), server_default=sa.text("'received'"), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_github_webhook_logs_delivery_id', 'github_webhook_logs', ['delivery_id'], unique=True)
        op.create_index('ix_github_webhook_logs_event_type', 'github_webhook_logs', ['event_type'], unique=False)
        op.create_index('ix_github_webhook_logs_repository_name', 'github_webhook_logs', ['repository_name'], unique=False)

    # 3. Create background_jobs table
    if 'background_jobs' not in tables:
        op.create_table(
            'background_jobs',
            sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('job_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=50), server_default=sa.text("'queued'"), nullable=False),
            sa.Column('progress_percent', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('params_json', sa.Text(), server_default=sa.text("'{}'"), nullable=False),
            sa.Column('result_json', sa.Text(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_background_jobs_user_id', 'background_jobs', ['user_id'], unique=False)
        op.create_index('ix_background_jobs_job_type', 'background_jobs', ['job_type'], unique=False)
        op.create_index('ix_background_jobs_status', 'background_jobs', ['status'], unique=False)

    # 4. Add columns to repositories table
    if 'repositories' in tables:
        repo_cols = [c['name'] for c in inspector.get_columns('repositories')]
        with op.batch_alter_table('repositories', schema=None) as batch_op:
            if 'github_repo_full_name' not in repo_cols:
                batch_op.add_column(sa.Column('github_repo_full_name', sa.String(length=255), nullable=True))
                batch_op.create_index('ix_repositories_github_repo_full_name', ['github_repo_full_name'], unique=False)
            if 'github_clone_url' not in repo_cols:
                batch_op.add_column(sa.Column('github_clone_url', sa.String(length=1024), nullable=True))
            if 'is_private' not in repo_cols:
                batch_op.add_column(sa.Column('is_private', sa.Boolean(), server_default=sa.text('0'), nullable=False))

    # 5. Add columns to analyses table
    if 'analyses' in tables:
        analysis_cols = [c['name'] for c in inspector.get_columns('analyses')]
        with op.batch_alter_table('analyses', schema=None) as batch_op:
            if 'pr_number' not in analysis_cols:
                batch_op.add_column(sa.Column('pr_number', sa.Integer(), nullable=True))
                batch_op.create_index('ix_analyses_pr_number', ['pr_number'], unique=False)
            if 'pr_title' not in analysis_cols:
                batch_op.add_column(sa.Column('pr_title', sa.String(length=512), nullable=True))
            if 'is_github_pr' not in analysis_cols:
                batch_op.add_column(sa.Column('is_github_pr', sa.Boolean(), server_default=sa.text('0'), nullable=False))
            if 'github_comment_id' not in analysis_cols:
                batch_op.add_column(sa.Column('github_comment_id', sa.String(length=100), nullable=True))
            if 'analysis_engine_version' not in analysis_cols:
                batch_op.add_column(sa.Column('analysis_engine_version', sa.String(length=50), server_default=sa.text("'1.0.0'"), nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'analyses' in tables:
        op.execute(sa.text("DROP TABLE IF EXISTS _alembic_tmp_analyses"))
        analysis_cols = [c['name'] for c in inspector.get_columns('analyses')]
        analysis_indexes = [i['name'] for i in inspector.get_indexes('analyses')]
        with op.batch_alter_table('analyses', schema=None) as batch_op:
            if 'ix_analyses_pr_number' in analysis_indexes:
                batch_op.drop_index('ix_analyses_pr_number')
            for col in ['analysis_engine_version', 'github_comment_id', 'is_github_pr', 'pr_title', 'pr_number']:
                if col in analysis_cols:
                    batch_op.drop_column(col)

    if 'repositories' in tables:
        op.execute(sa.text("DROP TABLE IF EXISTS _alembic_tmp_repositories"))
        repo_cols = [c['name'] for c in inspector.get_columns('repositories')]
        repo_indexes = [i['name'] for i in inspector.get_indexes('repositories')]
        with op.batch_alter_table('repositories', schema=None) as batch_op:
            if 'ix_repositories_github_repo_full_name' in repo_indexes:
                batch_op.drop_index('ix_repositories_github_repo_full_name')
            for col in ['is_private', 'github_clone_url', 'github_repo_full_name']:
                if col in repo_cols:
                    batch_op.drop_column(col)

    if 'background_jobs' in tables:
        op.drop_table('background_jobs')
    if 'github_webhook_logs' in tables:
        op.drop_table('github_webhook_logs')
    if 'github_accounts' in tables:
        op.drop_table('github_accounts')
