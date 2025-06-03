"""google_credentialsテーブルの追加

Revision ID: abcd1234
Revises: b24223c142f6
Create Date: 2025-05-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abcd1234'
down_revision = 'b24223c142f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'google_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('credentials_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_google_credentials_id'), 'google_credentials', ['id'], unique=False)
    op.create_index(op.f('ix_google_credentials_user_id'), 'google_credentials', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_google_credentials_user_id'), table_name='google_credentials')
    op.drop_index(op.f('ix_google_credentials_id'), table_name='google_credentials')
    op.drop_table('google_credentials')
