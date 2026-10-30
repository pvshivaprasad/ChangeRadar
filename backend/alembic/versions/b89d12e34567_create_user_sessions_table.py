"""create_user_sessions_table_and_repo_type

Revision ID: b89d12e34567
Revises: 436c296d7952
Create Date: 2026-10-30 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b89d12e34567'
down_revision: Union[str, Sequence[str], None] = '436c296d7952'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Create user_sessions table if missing
    if 'user_sessions' not in tables:
        op.create_table(
            'user_sessions',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('token_hash', sa.String(length=64), nullable=False),
            sa.Column('token_prefix', sa.String(length=16), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('last_accessed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('user_agent', sa.String(length=512), nullable=True),
            sa.Column('ip_address', sa.String(length=100), nullable=True),
        )
        op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'], unique=False)
        op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['token_hash'], unique=True)
        op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'], unique=False)

    # 2. Add repo_type to repositories if missing
    if 'repositories' in tables:
        repo_cols = [c['name'] for c in inspector.get_columns('repositories')]
        if 'repo_type' not in repo_cols:
            with op.batch_alter_table('repositories', schema=None) as batch_op:
                batch_op.add_column(sa.Column('repo_type', sa.String(length=50), server_default=sa.text("'local'"), nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'repositories' in tables:
        repo_cols = [c['name'] for c in inspector.get_columns('repositories')]
        if 'repo_type' in repo_cols:
            with op.batch_alter_table('repositories', schema=None) as batch_op:
                batch_op.drop_column('repo_type')

    if 'user_sessions' in tables:
        op.drop_table('user_sessions')
