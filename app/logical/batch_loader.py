# APP/LOGICAL/BATCH_LOADER.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload


# ## FUNCTIONS

def selectinload_batch_primary(records, relation):
    relation_property = getattr(records[0].__class__, relation).property
    lasttable = relation_property.mapper.class_
    primaryjoin = relation_property.primaryjoin
    record_id_gen = (getattr(item, primaryjoin.right.name) for item in records)
    last_items = lasttable.query.filter(primaryjoin.left.in_(record_id_gen)).all()
    for record in records:
        last_id = getattr(record, primaryjoin.right.name)
        last_item = next((item for item in last_items if getattr(item, primaryjoin.left.name) == last_id), None)
        record.__dict__[relation] = last_item
    return last_items


def selectinload_batch_secondary(records, relation):
    relation_property = getattr(records[0].__class__, relation).property
    primaryjoin = relation_property.primaryjoin
    nexttable = primaryjoin.right.table
    record_id_gen = (getattr(record, primaryjoin.left.name) for record in records)
    next_items = nexttable.query.filter(primaryjoin.right.in_(record_id_gen)).all2()
    lasttable = relation_property.mapper.class_
    secondaryjoin = relation_property.secondaryjoin
    secondary_id_gen = (getattr(item, secondaryjoin.right.name) for item in next_items)
    last_items = lasttable.query.filter(secondaryjoin.left.in_(secondary_id_gen)).all()
    for record in records:
        item_id = getattr(record, primaryjoin.left.name)
        next_item = next((item for item in next_items if getattr(item, primaryjoin.right.name) == item_id), None)
        if next_item is None:
            record.__dict__[relation] = None
            continue
        last_id = getattr(next_item, secondaryjoin.right.name)
        last_item = next((item for item in last_items if getattr(item, secondaryjoin.left.name) == last_id))
        record.__dict__[relation] = last_item
    return last_items


def selectinload_batch_relations(records, *relations):
    for relation in relations:
        relation_property = getattr(records[0].__class__, relation).property
        if relation_property.secondaryjoin is not None:
            records = selectinload_batch_secondary(records, relation)
        else:
            records = selectinload_batch_primary(records, relation)
