"""create_users_repositories_analyses_tables

Revision ID: 436c296d7952
Revises: 
Create Date: 2026-10-30 21:53:12.555952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '436c296d7952'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('api_token', sa.String(255), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
        op.create_index('ix_users_api_token', 'users', ['api_token'], unique=True)
    else:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('token_expires_at', sa.DateTime(), nullable=True))
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))

    if 'repositories' not in tables:
        op.create_table(
            'repositories',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('path', sa.String(1024), nullable=False),
            sa.Column('default_branch', sa.String(100), server_default=sa.text("'main'"), nullable=False),
            sa.Column('file_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('symbol_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('edge_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('is_archived', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('last_scanned_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_repositories_user_id', 'repositories', ['user_id'], unique=False)
        op.create_index('ix_repositories_path', 'repositories', ['path'], unique=False)
    else:
        with op.batch_alter_table('repositories', schema=None) as batch_op:
            batch_op.add_column(sa.Column('user_id', sa.Integer(), server_default=sa.text('1'), nullable=False))
            batch_op.add_column(sa.Column('is_archived', sa.Boolean(), server_default=sa.false(), nullable=False))
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
            batch_op.drop_index('ix_repositories_path')
            batch_op.create_index('ix_repositories_path', ['path'], unique=False)
            batch_op.create_index('ix_repositories_user_id', ['user_id'], unique=False)
            batch_op.create_foreign_key('fk_repositories_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')

    if 'analyses' not in tables:
        op.create_table(
            'analyses',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('repository_id', sa.Integer(), sa.ForeignKey('repositories.id', ondelete='SET NULL'), nullable=True),
            sa.Column('repo_name', sa.String(255), server_default=sa.text("''"), nullable=False),
            sa.Column('repo_path', sa.String(1024), server_default=sa.text("''"), nullable=False),
            sa.Column('base_commit', sa.String(100), nullable=False),
            sa.Column('head_commit', sa.String(100), nullable=False),
            sa.Column('status', sa.String(50), server_default=sa.text("'completed'"), nullable=False),
            sa.Column('risk_level', sa.String(50), server_default=sa.text("'low'"), nullable=False),
            sa.Column('risk_score', sa.Float(), server_default=sa.text('0.0'), nullable=False),
            sa.Column('changed_files_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('changed_symbols_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('impacted_symbols_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('recommended_tests_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
            sa.Column('summary_text', sa.Text(), server_default=sa.text("''"), nullable=False),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('report_json', sa.Text(), server_default=sa.text("'{}'"), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_analyses_user_id', 'analyses', ['user_id'], unique=False)
        op.create_index('ix_analyses_repository_id', 'analyses', ['repository_id'], unique=False)
    else:
        with op.batch_alter_table('analyses', schema=None) as batch_op:
            batch_op.add_column(sa.Column('user_id', sa.Integer(), server_default=sa.text('1'), nullable=False))
            batch_op.add_column(sa.Column('repo_name', sa.String(length=255), server_default=sa.text("''"), nullable=False))
            batch_op.add_column(sa.Column('repo_path', sa.String(length=1024), server_default=sa.text("''"), nullable=False))
            batch_op.add_column(sa.Column('status', sa.String(length=50), server_default=sa.text("'completed'"), nullable=False))
            batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
            batch_op.alter_column('repository_id', existing_type=sa.INTEGER(), nullable=True)
            batch_op.create_index('ix_analyses_user_id', ['user_id'], unique=False)
            batch_op.create_foreign_key('fk_analyses_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')
            batch_op.create_foreign_key('fk_analyses_repository_id', 'repositories', ['repository_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'analyses' in tables:
        op.drop_table('analyses')
    if 'repositories' in tables:
        op.drop_table('repositories')
    if 'users' in tables:
        op.drop_table('users')
