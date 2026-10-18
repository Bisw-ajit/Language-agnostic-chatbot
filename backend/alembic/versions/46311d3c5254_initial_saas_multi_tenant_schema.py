"""initial_saas_multi_tenant_schema

Revision ID: 46311d3c5254
Revises: 
Create Date: 2026-09-22 11:16:49.855072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46311d3c5254'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('analytics_daily', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_analytics_daily_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_foreign_key('fk_analytics_daily_tenant', 'organizations', ['tenant_id'], ['id'])

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_conversations_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_foreign_key('fk_conversations_tenant', 'organizations', ['tenant_id'], ['id'])

    with op.batch_alter_table('document_metadata', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_document_metadata_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_foreign_key('fk_document_metadata_tenant', 'organizations', ['tenant_id'], ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_foreign_key('fk_users_tenant', 'organizations', ['tenant_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_tenant', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_tenant_id'))
        batch_op.drop_column('tenant_id')

    with op.batch_alter_table('document_metadata', schema=None) as batch_op:
        batch_op.drop_constraint('fk_document_metadata_tenant', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_document_metadata_tenant_id'))
        batch_op.drop_column('tenant_id')

    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_conversations_tenant', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_conversations_tenant_id'))
        batch_op.drop_column('tenant_id')

    with op.batch_alter_table('analytics_daily', schema=None) as batch_op:
        batch_op.drop_constraint('fk_analytics_daily_tenant', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_analytics_daily_tenant_id'))
        batch_op.drop_column('tenant_id')
