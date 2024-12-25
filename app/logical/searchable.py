# APP/LOGICAL/SEARCHABLE.PY

# ## PYTHON IMPORTS
import re
import logging
from sqlalchemy import and_, not_, func
from sqlalchemy.orm import aliased, with_polymorphic, ColumnProperty, RelationshipProperty
from sqlalchemy.ext.associationproxy import ColumnAssociationProxyInstance, ObjectAssociationProxyInstance,\
    AmbiguousAssociationProxyInstance
from sqlalchemy.sql.expression import case
import sqlalchemy.sql.sqltypes as sqltypes

# ## PACKAGE IMPORTS
from config import DEBUG_LOG
from utility.data import is_truthy, is_falsey
from utility.time import process_utc_timestring

# ## LOCAL IMPORTS
from .. import SESSION
from ..models import base

# ## GLOBAL VARIABLES

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG_LOG else logging.WARNING)

TEXT_COMPARISON_TYPES = ['eq', 'ne', 'like', 'glob', 'not_like', 'not_glob', 'regex', 'not_regex']

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

def get_property(attr, name, model):
    if type(attr) in [ObjectAssociationProxyInstance, AmbiguousAssociationProxyInstance]:
        name = attr.target_collection
        attr = getattr(model, name)
    if not hasattr(attr, 'property'):
        raise Exception(f"Attribute {name} on model {model.__table__.name} is not a property.")
    return getattr(attr, 'property')


def get_attribute(model, name):
    if hasattr(model, name):
        value = getattr(model, name)
        if type(value) is ColumnAssociationProxyInstance:
            value = value.attr[0]
        return value


def get_attribute_property(model, name):
    attr = get_attribute(model, name)
    return get_property(attr, name, model) if attr is not None else None


def is_relationship(model, name):
    prop = get_attribute_property(model, name)
    return type(prop) is RelationshipProperty


def relationship_model(model, name):
    prop = get_attribute_property(model, name)
    return bool(prop) and prop.mapper.class_


def is_polymorphic(model, name):
    prop = get_attribute_property(model, name)
    return bool(prop) and prop.mapper.polymorphic_on is not None


def is_column(model, columnname):
    prop = get_attribute_property(model, columnname)
    return type(prop) is ColumnProperty


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
        base.IntEnum: 'ENUM',
        base.BlobMD5: 'STRING',
        base.EpochTimestamp: 'DATETIME',
        sqltypes.Integer: 'INTEGER',
        sqltypes.INTEGER: 'INTEGER',
        sqltypes.Float: 'FLOAT',
        sqltypes.DateTime: 'DATETIME',
        sqltypes.Boolean: 'BOOLEAN',
        sqltypes.String: 'STRING',
        sqltypes.Text: 'TEXT',
        sqltypes.TEXT: 'TEXT',
        sqltypes.Unicode: 'STRING',
        sqltypes.UnicodeText: 'TEXT',
    }
    column_type = type(getattr(model, columnname).property.columns[0].type)
    logger.debug('COLUMN-TYPE %s:%s as %s', model._table_name(), columnname, column_type)
    if column_type is not None:
        return switcher[column_type]
    else:
        raise Exception("%s - column of unexpected type: %s" % (columnname, str(column_type)))


# #### Main filter functions

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
        'ENUM': enum_filters,
        'BOOLEAN': boolean_filters,
        'STRING': text_filters,
        'TEXT': text_filters,
    }
    type = column_type(model, columnname)
    logger.debug('BASIC-FILTER %s:%s as %s with %s', model._table_name(), columnname, type, params)
    return switcher[type](model, columnname, params)


def relationship_attribute_filters(query, model, attribute, params):
    relation = get_attribute(model, attribute)
    relation_model = relationship_model(model, attribute)
    if is_polymorphic(model, attribute):
        if relation_model.polymorphic_base:
            return polymorphic_attribute_filters(query, model, attribute, params)
        # Else treat the relation like other relations
    filters = ()
    relation_property = get_property(relation, attribute, model)
    if (attribute + '_exists') in params:
        filters += relationship_exists_filters(model, attribute, params, relation_model, relation_property)
    elif ('has_' + attribute) in params:
        filters += relationship_has_filters(model, attribute, params, relation_property)
    elif ('count_' + attribute) in params:
        query = relationship_count_filters(model, attribute, params, relation_property, query)
    if attribute in params:
        if isinstance(params[attribute], str) and hasattr(model, attribute + '_enum'):
            params[attribute] = {'name': params[attribute]}
        if isinstance(params[attribute], dict):
            aliased_model = aliased(relation_model)
            query = query.unique_join(aliased_model, relation)
            attr_filters, query = all_attribute_filters(query, aliased_model, params[attribute])
            filters += (and_(*attr_filters),)
        else:
            logger.warning("RELATION-FILTER on %s with value %s is not a dict", attribute, params[attribute])
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


def enum_filters(model, columnname, params):
    filters = ()
    enum = getattr(model, columnname + '_enum')

    def _normalize_parameter(value):
        if isinstance(value, dict):
            temp = value.get('name')
            if temp is None:
                raise Exception("%s - only [name] subkey supported for enums" % columnname)
            value = temp
        subvalues = value.split(',')
        retvalues = []
        for v in subvalues:
            if v.isdigit() and int(v) in enum.values:
                retvalues.append(int(v))
            elif v in enum.names:
                retvalues.append(enum[v].value)
            else:
                raise Exception("%s - value is not a valid enum: %s" % (columnname, v))
        return retvalues

    if columnname in params:
        values = _normalize_parameter(params[columnname])
        filters += (getattr(model, columnname).in_(values),) if len(values) else ()
    if columnname + '_not' in params:
        values = _normalize_parameter(params[columnname + '_not'])
        filters += (not_(getattr(model, columnname).in_(values)),) if len(values) else ()
    if columnname + '_exists' in params:
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
        filters += (text_comparison_matching(model, columnname, params[param_key], cmp_type),)
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


# #### Relationship filter functions

def relationship_exists_filters(model, attribute, params, relation_model, relation_property):
    if relation_property.secondaryjoin is not None:
        raise Exception("Exists not available for secondary table relations. Use _has instead.")
    primaryjoin = relation_property.primaryjoin
    if primaryjoin.right.table == model.__table__:
        if is_truthy(params[attribute + '_exists']):
            return (primaryjoin.right.is_not(None),)
        elif is_falsey(params[attribute + '_exists']):
            return (primaryjoin.right.is_(None),)
        else:
            raise Exception("%s - value must be truthy or falsey" % (attribute + '_exists'))
    elif primaryjoin.left.table == model.__table__:
        subclause = relation_model.query.filter(primaryjoin.right.is_not(None)).with_entities(primaryjoin.right)
        if is_truthy(params[attribute + '_exists']):
            return (model.id.in_(subclause),)
        elif is_falsey(params[attribute + '_exists']):
            return (model.id.not_in(subclause),)
        else:
            raise Exception("%s - value must be truthy or falsey" % (attribute + '_exists'))
    else:
        raise Exception("Incorrect model configuration on %s with relation %s" % (repr(model), attribute))


def relationship_has_filters(model, attribute, params, relation_property):
    if relation_property.secondaryjoin is None:
        raise Exception("Has not available for fk relations. Use _exists instead.")
    primaryjoin = relation_property.primaryjoin
    subquery = SESSION.query(primaryjoin.right.table).with_entities(primaryjoin.right)
    subclause = model.id.in_(subquery)
    if is_truthy(params['has_' + attribute]):
        return (subclause,)
    elif is_falsey(params['has_' + attribute]):
        return (not_(subclause),)
    else:
        raise Exception("%s - value must be truthy or falsey" % ('has_' + attribute))


def relationship_count_filters(model, attribute, params, relation_property, query):
    primaryjoin = relation_property.primaryjoin
    if relation_property.secondaryjoin is None:
        rightside = primaryjoin.left
        query = query.join(primaryjoin.right.table, primaryjoin)
    else:
        rightside = primaryjoin.right
        query = query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right)
    value = params['count_' + attribute]
    count_clause = relationship_count(model, rightside, value)
    if count_clause is not None:
        return query.group_by(model).having(count_clause)
    else:
        raise Exception("%s - invalid value: %s" % ('count_' + attribute, value))


# #### Type auxiliary functions

def relationship_count(model, rightside, value):
    match = re.match(r'^\d+$', value)
    if match:
        return func.count(rightside) == int(value)
    match = re.match(r'^<=(\d+)$', value)
    if match:
        return func.count(rightside) <= int(match.group(1))
    match = re.match(r'^<(\d+)$', value)
    if match:
        return func.count(rightside) < int(match.group(1))
    match = re.match(r'^>=(\d+)$', value)
    if match:
        return func.count(rightside) >= int(match.group(1))
    match = re.match(r'^>(\d+)$', value)
    if match:
        return func.count(rightside) > int(match.group(1))
    match = re.match(r'^!=(\d+)$', value)
    if match:
        return func.count(rightside) != int(match.group(1))


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
        return getattr(model, columnname).is_(None)
    if value == 'none':
        return getattr(model, columnname).is_not(None)
    return getattr(model, columnname) == parser(value)


def text_comparison_matching(model, columnname, value, cmp_type):
    if cmp_type == 'eq':
        return getattr(model, columnname) == value
    if cmp_type == 'ne':
        return getattr(model, columnname) != value
    if cmp_type == 'like':
        return getattr(model, columnname).like(sql_excape(value), escape='\x01')
    if cmp_type == 'glob':
        return getattr(model, columnname).op('GLOB')(value)
    if cmp_type == 'not_like':
        return getattr(model, columnname).not_like(sql_excape(value), escape='\x01')
    if cmp_type == 'not_glob':
        return getattr(model, columnname).op('NOT GLOB')(value)
    if cmp_type == 'regex':
        return getattr(model, columnname).regexp_match(value)
    if cmp_type == 'not_regex':
        return not_(getattr(model, columnname).regexp_match(value))


def existence_matching(model, columnname, value):
    if is_truthy(value):
        return getattr(model, columnname).is_not(None)
    elif is_falsey(value):
        return getattr(model, columnname).is_(None)
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
        return (getattr(model, columnname).is_(True),)
    if is_falsey(value):
        return (getattr(model, columnname).is_(False),)
    raise Exception("%s - value must be truthy or falsey" % columnname)


# #### Main order functions

def order_attributes(query, model, order_params):
    attributes = model.order_attributes
    basic_attributes = [attribute for attribute in attributes if is_column(model, attribute)]
    basic_orders = ()
    if type(order_params) is not list:
        order_params = [order_params]
    basic_order_params = [param for param in order_params if type(param) is str]
    for param in basic_order_params:
        for attribute in basic_attributes:
            basic_orders += basic_attribute_orders(model, attribute, param)
    return query.order_by(*basic_orders)


def basic_attribute_orders(model, columnname, param):
    if param == columnname or param == columnname + '_asc':
        return (getattr(model, columnname).asc(),)
    if param == columnname + '_desc':
        return (getattr(model, columnname).desc(),)
    if param == columnname + '_nulls_first' or param == columnname + '_asc_nulls_first':
        return (getattr(model, columnname).asc().nulls_first(),)
    if param == columnname + '_nulls_last' or param == columnname + '_asc_nulls_last':
        return (getattr(model, columnname).asc().nulls_last(),)
    if param == columnname + '_desc_nulls_first':
        return (getattr(model, columnname).desc().nulls_first(),)
    if param == columnname + '_desc_nulls_last':
        return (getattr(model, columnname).desc().nulls_last(),)
    return ()


def custom_order(query, model, search):
    ids = [int(id) for id in search.get('id', "").split(',') if id.isdigit()]
    if len(ids) == 0:
        return None
    order_clause = case(
        {id: index for index, id in enumerate(ids)},
        value=model.id,
    )
    return query.order_by(order_clause)
