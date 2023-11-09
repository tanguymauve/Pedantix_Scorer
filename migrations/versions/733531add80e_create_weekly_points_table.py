"""Create weekly_points table

Revision ID: 733531add80e
Revises: 12c32957264b
Create Date: 2023-11-09 22:09:59.282626

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '733531add80e'
down_revision = '12c32957264b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('weekly_points',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('combined_points', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('weekly_points')
    # ### end Alembic commands ###