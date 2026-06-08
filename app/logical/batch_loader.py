# APP/LOGICAL/BATCH_LOADER.PY


# ## FUNCTIONS

def selectinload_batch_primary(records, relation):
    relation_property = getattr(records[0].__class__, relation).property
    reverse = relation_property.primaryjoin.left.table == records[0].__table__
    lasttable = relation_property.mapper.class_
    primaryjoin = relation_property.primaryjoin
    primaryjoin_left, primaryjoin_right =\
        (primaryjoin.left, primaryjoin.right)\
        if not reverse else\
        (primaryjoin.right, primaryjoin.left)
    record_id_set = set(getattr(item, primaryjoin_right.name) for item in records)
    load_items = lasttable.query.filter(primaryjoin_left.in_(record_id_set)).all()
    for record in records:
        record_id = getattr(record, primaryjoin_right.name)
        if relation_property.uselist:
            assign_item = [item for item in load_items if getattr(item, primaryjoin_left.name) == record_id]
        else:
            assign_item = next((item for item in load_items if getattr(item, primaryjoin_left.name) == record_id), None)
        record.__dict__[relation] = assign_item
    return load_items


def selectinload_batch_secondary(records, relation):
    relation_property = getattr(records[0].__class__, relation).property
    primaryjoin = relation_property.primaryjoin
    nexttable = primaryjoin.right.table
    record_id_set = set(getattr(record, primaryjoin.left.name) for record in records)
    next_items = nexttable.query.filter(primaryjoin.right.in_(record_id_set)).all2()
    lasttable = relation_property.mapper.class_
    secondaryjoin = relation_property.secondaryjoin
    secondary_id_set = set(getattr(item, secondaryjoin.right.name) for item in next_items)
    last_items = lasttable.query.filter(secondaryjoin.left.in_(secondary_id_set)).all()
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


def selectinload_includes(records, includes):
    for relation in includes:
        model = records[0].model
        if relation not in model.relations:
            continue
        relation_property = getattr(model, relation).property
        if relation_property.secondaryjoin is not None:
            relation_records = selectinload_batch_secondary(records, relation)
        else:
            relation_records = selectinload_batch_primary(records, relation)
        if len(relation_records):
            selectinload_includes(relation_records, includes[relation])
