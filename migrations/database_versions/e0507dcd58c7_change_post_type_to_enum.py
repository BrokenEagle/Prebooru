"""Change post type to enum

Revision ID: e0507dcd58c7
Revises: 650eb82244ee
Create Date: 2022-09-15 20:04:39.455543

"""
# ## PYTHON IMPORTS
import re

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'e0507dcd58c7'
down_revision = '650eb82244ee'
branch_labels = None
depends_on = None

TYPE_RG = re.compile('user|subscription')


# ## FUNCTIONS

def init():
    global PostType
    from app.models.post import PostType


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    init()
    t_post = sa.Table(
        'post',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('type', sa.String),
        sa.Column('temp', sa.Integer),
    )

    print("Adding temp column")
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.Integer(), nullable=True))

    print("Populating temp column")
    connection = op.get_bind()
    index = 0
    while True:
        post_data = connection.execute(sa.select([t_post.c.id, t_post.c.type]).limit(1000).offset(index * 1000)).fetchall()
        for post in post_data:
            enum_name = TYPE_RG.match(post[1]).group(0)
            enum_value = PostType[enum_name].value
            connection.execute(t_post.update().where(t_post.c.id == post[0]).values(
                temp=enum_value,
                ))
        if len(post_data):
            print(f"post #{post_data[0][0]} - post #{post_data[-1][0]}")
        if len(post_data) < 1000:
            break
        index += 1

    print("Dropping type column")
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_column('type')

    print("Renaming temp column to type")
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('temp',
                              new_column_name='type',
                              existing_type=sa.INTEGER(),
                              nullable=False
                              )


def downgrade_():
    print("Initializing")
    init()
    t_post = sa.Table(
        'post',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('type', sa.Integer),
        sa.Column('temp', sa.String),
    )

    print("Adding temp column")
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.VARCHAR(length=50), nullable=True))

    print("Populating temp column")
    connection = op.get_bind()
    index = 0
    while True:
        post_data = connection.execute(sa.select([t_post.c.id, t_post.c.type]).limit(1000).offset(index * 1000)).fetchall()
        for post in post_data:
            enum_name = PostType(post[1]).name
            type_string = enum_name + '_post'
            connection.execute(t_post.update().where(t_post.c.id == post[0]).values(
                temp=type_string,
                ))
        if len(post_data):
            print(f"post #{post_data[0][0]} - post #{post_data[-1][0]}")
        if len(post_data) < 1000:
            break
        index += 1

    print("Dropping old type column")
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_column('type')

    print("Renaming temp column to type")
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.alter_column('temp',
                              new_column_name='type',
                              existing_type=sa.VARCHAR(),
                              nullable=False
                              )
