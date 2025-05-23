"""empty message

Revision ID: 4aee60889b3d
Revises: fb22afda156f
Create Date: 2025-04-23 17:57:28.302143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4aee60889b3d'
down_revision = 'fb22afda156f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('data_plots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('data_file_id', sa.Integer(), nullable=False))
        batch_op.drop_constraint('data_plots_analysis_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'data_files', ['data_file_id'], ['id'])
        batch_op.drop_column('analysis_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('data_plots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('analysis_id', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('data_plots_analysis_id_fkey', 'data_analyses', ['analysis_id'], ['id'])
        batch_op.drop_column('data_file_id')

    # ### end Alembic commands ###
