# APP/LOGICAL/SEARCHABLE.PY

# ## PYTHON IMPORTS
import re
from sqlalchemy import and_, not_, func
from sqlalchemy.orm import aliased, with_polymorphic
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.ext.associationproxy import ColumnAssociationProxyInstance
import sqlalchemy.sql.sqltypes as sqltypes

# ## PACKAGE IMPORTS
from utility.data import is_truthy, is_falsey
from utility.time import process_utc_timestring


# ## GLOBAL VARIABLES

TEXT_COMPARISON_TYPES = ['eq', 'ne', 'like', 'ilike', 'not_like', 'not_ilike', 'regex', 'not_regex']

COMMA_ARRAY_TYPES = ['comma', 'lower_comma', 'not_comma', 'not_lower_comma']
SPACE_ARRAY_TYPES = ['space', 'lower_space', 'not_space', 'not_lower_space']
LOWER_ARRAY_TYPES = ['lower_array', 'lower_comma', 'lower_space', 'not_lower_array', 'not_lower_comma',
                     'not_lower_space']
NOT_ARRAY_TYPES = ['not_array', 'not_comma', 'not_space', 'not_lower_array', 'not_lower_comma', 'not_lower_space']
ALL_ARRAY_TYPES = ['array', 'comma', 'space', 'not_array', 'not_comma', 'not_space', 'lower_array', 'lower_comma',
                   'lower_space', 'not_lower_array', 'not_lower_comma', 'not_lower_space']

TEXT_COMPARISON_RE = r'%%s_(%s)' % '|'.join(TEXT_COMPARISON_TYPES)
TEXT_ARRAY_RE = '%%s_(%s)' % '|'.join(ALL_ARRAY_TYPES)


# ## FUNCTIONS

# #### Test functions

def get_attribute(model, columnname):
    if hasattr(model, columnname):
        value = getattr(model, columnname)
        if type(value) is ColumnAssociationProxyInstance:
            value = value.attr[0]
        return value


def is_relationship(model, columnname):
    attr = get_attribute(model, columnname)
    return attr and type(attr.property) is RelationshipProperty


def relationship_model(model, attribute):
    return get_attribute(model, attribute).property.mapper.class_


def is_polymorphic(model, attribute):
    return get_attribute(model, attribute).property.mapper.polymorphic_on is not None


def is_column(model, columnname):
    return columnname in model.__table__.c.keys()


def is_polymorphic_column(model, columnname):
    return hasattr(model, 'polymorphic_columns') and columnname in model.polymorphic_columns


# #### Helper functions

def sql_excape(value):
    retvalue = value.replace('%', '\x01%')
    retvalue = retvalue.replace('_', '\x01_')
    retvalue = re.sub(r'(?<!\\)\*', '%', retvalue)
    retvalue = retvalue.replace(r'\*', '*')
    return retvalue


def parse_cast(value, type):
    if type == 'INTEGER':
        return int(value)
    if type == 'DATETIME':
        return process_utc_timestring(value)
    if type == 'FLOAT':
        return float(value)
    return value


def column_type(model, columnname):
    switcher = {
        sqltypes.Integer: 'INTEGER',
        sqltypes.Float: 'FLOAT',
        sqltypes.DateTime: 'DATETIME',
        sqltypes.Boolean: 'BOOLEAN',
        sqltypes.String: 'STRING',
        sqltypes.Text: 'TEXT',
        sqltypes.Unicode: 'STRING',
        sqltypes.UnicodeText: 'TEXT',
    }
    column_type = type(getattr(model.__table__.c, columnname).type)
    try:
        return switcher[column_type]
    except Exception:
        raise Exception("%s - column of unexpected type: %s" % (columnname, str(column_type)))


# #### Main execution functions

def search_attributes(query, model, params):
    all_filters, query = all_attribute_filters(query, model, params)
    query = query.filter(*all_filters)
    return query


def all_attribute_filters(query, model, params):
    attributes = model.searchable_attributes
    basic_attributes = [attribute for attribute in attributes if is_column(model, attribute)]
    basic_filters = ()
    for attribute in basic_attributes:
        basic_model = model if not is_polymorphic_column(model, attribute) else model.polymorphic_columns[attribute]
        basic_filters += basic_attribute_filters(basic_model, attribute, params)
    relationship_attributes = [attribute for attribute in attributes if is_relationship(model, attribute)]
    relationship_filters = ()
    for attribute in relationship_attributes:
        filters, query = relationship_attribute_filters(query, model, attribute, params)
        relationship_filters += filters
    return (basic_filters + relationship_filters), query


def basic_attribute_filters(model, columnname, params):
    switcher = {
        'INTEGER': numeric_filters,
        'DATETIME': numeric_filters,
        'FLOAT': numeric_filters,
        'BOOLEAN': boolean_filters,
        'STRING': text_filters,
        'TEXT': text_filters,
    }
    type = column_type(model, columnname)
    return switcher[type](model, columnname, params)


def relationship_attribute_filters(query, model, attribute, params):
    relation = get_attribute(model, attribute)
    relation_model = relationship_model(model, attribute)
    if is_polymorphic(model, attribute) and relation_model.polymorphic_base:
        return polymorphic_attribute_filters(query, model, attribute, params)
    filters = ()
    if ('has_' + attribute) in params:
        primaryjoin = relation.property.primaryjoin
        subquery = model.query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right)\
                        .filter(primaryjoin.left == primaryjoin.right).with_entities(model.id)
        subclause = model.id.in_(subquery)
        if is_truthy(params['has_' + attribute]):
            filters += (subclause,)
        elif is_falsey(params['has_' + attribute]):
            filters += (not_(subclause),)
        else:
            raise Exception("%s - value must be truthy or falsey" % ('has_' + attribute))
    elif ('count_' + attribute) in params:
        primaryjoin = relation.property.primaryjoin
        value = params['count_' + attribute]
        count_clause = relationship_count(model, primaryjoin, value)
        if count_clause is not None:
            query = query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right).group_by(model)\
                         .having(count_clause)
        else:
            raise Exception("%s - invalid value: %s" % ('count_' + attribute, value))
    if attribute in params:
        aliased_model = aliased(relation_model)
        query = query.unique_join(aliased_model, relation)
        attr_filters, query = all_attribute_filters(query, aliased_model, params[attribute])
        filters += (and_(*attr_filters),)
    return filters, query


def polymorphic_attribute_filters(query, model, attribute, params):
    if attribute not in params:
        return (), query
    relation = get_attribute(model, attribute)
    relation_model = relationship_model(model, attribute)
    subclass_names = [subclass.__name__ for subclass in relation_model.polymorphic_classes]
    subclass_attributes = set(params[attribute].keys()).intersection(subclass_names)
    if not isinstance(params[attribute], dict) or not subclass_attributes:
        raise Exception("Must include subclass designation for polymorphic class: %s" % repr(subclass_names))
    polymorphic_model = with_polymorphic(relation_model, relation_model.polymorphic_classes)
    query = query.unique_join(polymorphic_model, relation)
    for key in subclass_attributes:
        filters = ()
        attr_filters, query = all_attribute_filters(query, getattr(polymorphic_model, key), params[attribute][key])
        filters += (and_(*attr_filters),)
    return filters, query


# #### Type filter functions

def numeric_filters(model, columnname, params):
    type = column_type(model, columnname)
    filters = ()
    if columnname in params:
        filters += (numeric_matching(model, columnname, params[columnname]),)
    if (columnname + '_not') in params:
        filters += (not_(numeric_matching(model, columnname, params[columnname + '_not'])),)
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == parse_cast(params[columnname + '_eq'], type),)
    if (columnname + '_ne') in params:
        filters += (getattr(model, columnname) != parse_cast(params[columnname + '_ne'], type),)
    if (columnname + '_gt') in params:
        filters += (getattr(model, columnname) > parse_cast(params[columnname + '_gt'], type),)
    if (columnname + '_ge') in params:
        filters += (getattr(model, columnname) >= parse_cast(params[columnname + '_ge'], type),)
    if (columnname + '_lt') in params:
        filters += (getattr(model, columnname) < parse_cast(params[columnname + '_lt'], type),)
    if (columnname + '_le') in params:
        filters += (getattr(model, columnname) <= parse_cast(params[columnname + '_le'], type),)
    if (columnname + '_exists') in params:
        filters += (existence_matching(model, columnname, params[columnname + '_exists']),)
    return filters


def text_filters(model, columnname, params):
    filters = ()
    if columnname in params:
        filters += (getattr(model, columnname) == params[columnname],)
    cmp_regex = re.compile(TEXT_COMPARISON_RE % columnname)
    cmp_matches = [cmp_regex.match(key) for key in params.keys()]
    cmp_types = [match.group(1) for match in cmp_matches if match is not None]
    for cmp_type in cmp_types:
        param_key = columnname + '_' + cmp_type
        filters += (text_comparion_matching(model, columnname, params[param_key], cmp_type),)
    if (columnname + '_exists') in params:
        filters += (existence_matching(model, columnname, params[columnname + '_exists']),)
    array_regex = re.compile(TEXT_ARRAY_RE % columnname)
    array_matches = [array_regex.match(key) for key in params.keys()]
    array_types = [match.group(1) for match in array_matches if match is not None]
    for array_type in array_types:
        param_key = columnname + '_' + array_type
        filters += (text_array_matching(model, columnname, params[param_key], array_type),)
    return filters


def boolean_filters(model, columnname, params):
    if columnname in params:
        return boolean_matching(model, columnname, params[columnname])
    return ()


# #### Type auxiliary functions

def relationship_count(model, primaryjoin, value):
    match = re.match(r'^\d+$', value)
    if match:
        return func.count(primaryjoin.right) == int(value)
    match = re.match(r'^<=(\d+)$', value)
    if match:
        return func.count(primaryjoin.right) <= int(match.group(1))
    match = re.match(r'^<(\d+)$', value)
    if match:
        return func.count(primaryjoin.right) < int(match.group(1))
    match = re.match(r'^>=(\d+)$', value)
    if match:
        return func.count(primaryjoin.right) >= int(match.group(1))
    match = re.match(r'^>(\d+)$', value)
    if match:
        return func.count(primaryjoin.right) > int(match.group(1))
    match = re.match(r'^!=(\d+)$', value)
    if match:
        return func.count(primaryjoin.right) != int(match.group(1))


def numeric_matching(model, columnname, value):
    type = column_type(model, columnname)

    def parser(value):
        nonlocal type
        return parse_cast(value, type)

    match = re.match(r'(.+?)\.\.(.+)', value)
    if match:
        return getattr(model, columnname).between(*map(parser, re.match(r'(.+?)\.\.(.+)', value).groups()))
    match = re.match(r'<=(.+)', value) or re.match(r'\.\.(.+)', value)
    if match:
        return getattr(model, columnname) <= parser(match.group(1))
    match = re.match(r'<(.+)', value)
    if match:
        return getattr(model, columnname) < parser(match.group(1))
    match = re.match(r'>=(.+)', value) or re.match(r'(.+)\.\.$', value)
    if match:
        return getattr(model, columnname) >= parser(match.group(1))
    match = re.match(r'>(.+)', value)
    if match:
        return getattr(model, columnname) > parser(match.group(1))
    if re.search(r'[ ,]', value):
        return getattr(model, columnname).in_(map(parser, re.split(r'[ ,]', value)))
    if value == 'any':
        return getattr(model, columnname).__ne__(None)
    if value == 'none':
        return getattr(model, columnname).__eq__(None)
    return getattr(model, columnname) == parser(value)


def text_comparion_matching(model, columnname, value, cmp_type):
    if cmp_type == 'eq':
        return getattr(model, columnname) == value
    if cmp_type == 'ne':
        return getattr(model, columnname) != value
    if cmp_type == 'like':
        return getattr(model, columnname).like(sql_excape(value), escape='\x01')
    if cmp_type == 'ilike':
        return getattr(model, columnname).ilike(sql_excape(value), escape='\x01')
    if cmp_type == 'not_like':
        return not_(getattr(model, columnname).like(sql_excape(value), escape='\x01'))
    if cmp_type == 'not_ilike':
        return not_(getattr(model, columnname).ilike(sql_excape(value), escape='\x01'))
    if cmp_type == 'regex':
        return getattr(model, columnname).regexp_match(value)
    if cmp_type == 'not_regex':
        return not_(getattr(model, columnname).regexp_match(value))


def existence_matching(model, columnname, value):
    if is_truthy(value):
        return getattr(model, columnname).__ne__(None)
    elif is_falsey(value):
        return getattr(model, columnname).__eq__(None)
    else:
        raise Exception("%s - value must be truthy or falsey" % (columnname + '_exists'))


def text_array_matching(model, columnname, value, array_type):
    if array_type in COMMA_ARRAY_TYPES:
        value_array = value.split(',')
    elif array_type in SPACE_ARRAY_TYPES:
        value_array = value.split(' ')
    else:
        value_array = value
    if array_type in LOWER_ARRAY_TYPES:
        value_array = [value.lower() for value in value_array]
    if array_type not in NOT_ARRAY_TYPES and array_type not in LOWER_ARRAY_TYPES:
        return getattr(model, columnname).in_(value_array)
    if array_type in NOT_ARRAY_TYPES and array_type not in LOWER_ARRAY_TYPES:
        return not_(getattr(model, columnname).in_(value_array))
    if array_type not in NOT_ARRAY_TYPES and array_type in LOWER_ARRAY_TYPES:
        return func.lower(getattr(model, columnname)).in_(value_array)
    if array_type in NOT_ARRAY_TYPES and array_type in LOWER_ARRAY_TYPES:
        return not_(func.lower(getattr(model, columnname)).in_(value_array))


def boolean_matching(model, columnname, value):
    if is_truthy(value):
        return (getattr(model, columnname).__eq__(True),)
    if is_falsey(value):
        return (getattr(model, columnname).__eq__(False),)
    raise Exception("%s - value must be truthy or falsey" % columnname)
