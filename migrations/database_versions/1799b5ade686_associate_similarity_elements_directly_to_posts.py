# MIGRATIONS/VERSIONS/1799B5ADE686_ASSOCIATE_SIMILARITY_ELEMENTS_DIRECTLY_TO_POSTS.PY
"""Associate similarity elements directly to posts

Revision ID: 1799b5ade686
Revises: ba9d1752c724
Create Date: 2022-10-08 09:46:36.464108

"""

# EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from migrations.tables import remove_temp_tables
from migrations.constraints import create_constraint, drop_constraint


# GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '1799b5ade686'
down_revision = 'ba9d1752c724'
branch_labels = None
depends_on = None

t_similarity_element = sa.Table(
    'similarity_pool_element',
    sa.MetaData(),
    sa.Column('id', sa.Integer),
    sa.Column('pool_id', sa.Integer),
)

t_similarity_pool = sa.Table(
    'similarity_pool',
    sa.MetaData(),
    sa.Column('id', sa.Integer),
    sa.Column('post_id', sa.Integer),
    sa.Column('created', sa.DATETIME),
    sa.Column('updated', sa.DATETIME),
    sa.Column('element_count', sa.INTEGER),
)


# FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Removing temp tables")
    remove_temp_tables(['similarity_pool_element'])

    print("Dropping pool constraint")
    drop_constraint('similarity_pool_element', 'fk_similarity_pool_element_pool_id_similarity_pool', 'foreignkey')

    print("Repopulating pool_id column")
    connection = op.get_bind()
    index = 0
    while True:
        element_data = connection.execute(sa.select([t_similarity_element.c.id, t_similarity_element.c.pool_id]).order_by(t_similarity_element.c.id.asc()).limit(1000).offset(index * 1000)).fetchall()
        element_data = [{'id': element[0], 'pool_id': element[1]} for element in element_data]
        if len(element_data):
            print(f"similarity element #{element_data[0]['id']} - similarity_element #{element_data[-1]['id']}")
        pool_ids = set(element['pool_id'] for element in element_data)
        pool_data = connection.execute(sa.select([t_similarity_pool.c.id, t_similarity_pool.c.post_id]).where(t_similarity_pool.c.id.in_(pool_ids))).fetchall()
        pool_data = [{'id': pool[0], 'post_id': pool[1]} for pool in pool_data]
        for element in element_data:
            pool = next((pool for pool in pool_data if pool['id'] == element['pool_id']))
            connection.execute(t_similarity_element.update().where(t_similarity_element.c.id == element['id']).values(
                pool_id=pool['post_id'],
                ))
        if len(element_data) < 1000:
            break
        index += 1

    print("Creating pool constraint")
    create_constraint('similarity_pool_element', 'fk_similarity_pool_element_pool_id_post', 'foreignkey', ('post', ['pool_id'], ['id']))

    print("Dropping similarity pool")
    op.drop_table('similarity_pool')


def downgrade_():
    print("Removing temp tables")
    remove_temp_tables(['similarity_pool', 'similarity_pool_element'])

    print("Creating similarity pool")
    op.create_table('similarity_pool',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('post_id', sa.INTEGER(), nullable=False),
        sa.Column('created', sa.DATETIME(), nullable=False),
        sa.Column('updated', sa.DATETIME(), nullable=False),
        sa.Column('element_count', sa.INTEGER(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['post.id'], name='fk_similarity_pool_post_id_post'),
        sa.PrimaryKeyConstraint('id', name='pk_similarity_pool'),
    )

    print("Dropping pool constraint")
    drop_constraint('similarity_pool_element', 'fk_similarity_pool_element_pool_id_post', 'foreignkey')

    print("Adding similarity pools")
    connection = op.get_bind()
    existing_post_ids = set()
    index = 0
    while True:
        element_data = connection.execute(sa.select([t_similarity_element.c.id, t_similarity_element.c.pool_id]).order_by(t_similarity_element.c.id.asc()).limit(1000).offset(index * 1000)).fetchall()
        element_data = [{'id': element[0], 'pool_id': element[1]} for element in element_data]
        if len(element_data):
            print(f"similarity element #{element_data[0]['id']} - similarity element #{element_data[-1]['id']}")
        post_ids = set(element['pool_id'] for element in element_data)
        create_post_ids = post_ids.difference(existing_post_ids)
        for post_id in create_post_ids:
            current_time = get_current_time()
            pool = connection.execute(t_similarity_pool.insert().values({
                'post_id': post_id,
                'created': current_time,
                'updated': current_time,
                'element_count': 0,
                }))
        pool_data = connection.execute(sa.select([t_similarity_pool.c.id, t_similarity_pool.c.post_id]).where(t_similarity_pool.c.post_id.in_(post_ids))).fetchall()
        pool_data = [{'id': pool[0], 'post_id': pool[1]} for pool in pool_data]
        for element in element_data:
            pool = next((pool for pool in pool_data if pool['post_id'] == element['pool_id']))
            connection.execute(t_similarity_element.update().where(t_similarity_element.c.id == element['id']).values(
                pool_id=pool['id'],
                ))
        if len(element_data) < 1000:
            break
        index += 1
        existing_post_ids.update(post_ids)

    print("Setting the element counts")
    index = 0
    while True:
        pool_data = connection.execute(sa.select([t_similarity_pool.c.id]).order_by(t_similarity_pool.c.id.asc()).limit(1000).offset(index * 1000)).fetchall()
        pool_ids = [data[0] for data in pool_data]
        if len(pool_ids):
            print(f"similarity pool #{pool_ids[0]} - similarity pool #{pool_ids[0]}")
        for pool_id in pool_ids:
            element_count = len(connection.execute(sa.select([t_similarity_element.c.id]).where(t_similarity_element.c.pool_id == pool_id)).fetchall())
            connection.execute(t_similarity_pool.update().where(t_similarity_pool.c.id == pool_id).values(
                element_count=element_count,
                ))
        if len(pool_data) < 1000:
            break
        index += 1

    print("Creating pool constraint")
    create_constraint('similarity_pool_element', 'fk_similarity_pool_element_pool_id_similarity_pool', 'foreignkey', ('similarity_pool', ['pool_id'], ['id']))
