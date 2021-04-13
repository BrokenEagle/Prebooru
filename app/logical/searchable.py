# APP/LOGICAL/UNSHORTEN_LINK.PY

# ##PYTHON IMPORTS
import re
from sqlalchemy import and_, not_, func
import sqlalchemy.sql.sqltypes as sqltypes
from sqlalchemy.orm import aliased
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy import func as sqlfuncs

# ##LOCAL IMPORTS
from .utility import IsTruthy, IsFalsey, ProcessUTCTimestring


# ##GLOBAL VARIABLES

TEXT_COMPARISON_TYPES = ['eq', 'ne', 'like', 'ilike', 'not_like', 'not_ilike', 'regex', 'not_regex']

COMMA_ARRAY_TYPES = ['comma', 'lower_comma', 'not_comma', 'not_lower_comma']
SPACE_ARRAY_TYPES = ['space', 'lower_space', 'not_space', 'not_lower_space']
LOWER_ARRAY_TYPES = ['lower_array', 'lower_comma', 'lower_space', 'not_lower_array', 'not_lower_comma', 'not_lower_space']
NOT_ARRAY_TYPES = ['not_array', 'not_comma', 'not_space', 'not_lower_array', 'not_lower_comma', 'not_lower_space']
ALL_ARRAY_TYPES = ['array', 'comma', 'space', 'not_array', 'not_comma', 'not_space', 'lower_array', 'lower_comma',
                   'lower_space', 'not_lower_array', 'not_lower_comma', 'not_lower_space']

TEXT_COMPARISON_RE = r'%%s_(%s)' % '|'.join(TEXT_COMPARISON_TYPES)
TEXT_ARRAY_RE = '%%s_(%s)' % '|'.join(ALL_ARRAY_TYPES)


# ##FUNCTIONS

# #### Test functions

def IsRelationship(model, columnname):
    return hasattr(model, columnname) and type(getattr(model, columnname).property) is RelationshipProperty


def RelationshipModel(model, attribute):
    return getattr(model, attribute).property.mapper.class_


def IsPolymorphic(model, attribute):
    return getattr(model, attribute).property.mapper.polymorphic_on is not None


def IsColumn(model, columnname):
    return columnname in model.__table__.c.keys()


def IsPolymorphicColumn(model, columnname):
    return hasattr(model, 'polymorphic_columns') and columnname in model.polymorphic_columns


# #### Helper functions

def SQLEscape(value):
    retvalue = value.replace('%', '\x01%')
    retvalue = retvalue.replace('_', '\x01_')
    retvalue = re.sub(r'(?<!\\)\*', '%', retvalue)
    retvalue = retvalue.replace(r'\*', '*')
    return retvalue


def ParseCast(value, type):
    if type == 'INTEGER':
        return int(value)
    if type == 'DATETIME':
        return ProcessUTCTimestring(value)
    if type == 'FLOAT':
        return float(value)
    return value


def ColumnType(model, columnname):
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

def SearchAttributes(query, model, params):
    all_filters, query = AllAttributeFilters(query, model, params)
    query = query.filter(*all_filters)
    return query


def AllAttributeFilters(query, model, params):
    attributes = model.searchable_attributes
    basic_attributes = [attribute for attribute in attributes if IsColumn(model, attribute)]
    basic_filters = ()
    for attribute in basic_attributes:
        print(attribute, IsPolymorphicColumn(model, attribute))
        basic_model = model if not IsPolymorphicColumn(model, attribute) else model.polymorphic_columns[attribute]
        basic_filters += BasicAttributeFilters(basic_model, attribute, params)
    relationship_attributes = [attribute for attribute in attributes if IsRelationship(model, attribute)]
    relationship_filters = ()
    for attribute in relationship_attributes:
        filters, query = RelationAttributeFilters(query, model, attribute, params)
        relationship_filters += filters
    return (basic_filters + relationship_filters), query


def BasicAttributeFilters(model, columnname, params):
    switcher = {
        'INTEGER': NumericFilters,
        'DATETIME': NumericFilters,
        'FLOAT': NumericFilters,
        'BOOLEAN': BooleanFilters,
        'STRING': TextFilters,
        'TEXT': TextFilters,
    }
    type = ColumnType(model, columnname)
    return switcher[type](model, columnname, params)


def RelationAttributeFilters(query, model, attribute, params):
    if IsPolymorphic(model, attribute):
        raise Exception("%s - polymorphic relationships are currently unhandled" % attribute)
    relation = getattr(model, attribute)
    filters = ()
    if ('has_' + attribute) in params:
        primaryjoin = relation.property.primaryjoin
        subquery = model.query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right).filter(primaryjoin.left == primaryjoin.right).with_entities(model.id)
        subclause = model.id.in_(subquery)
        if IsTruthy(params['has_' + attribute]):
            filters += (subclause,)
        elif IsFalsey(params['has_' + attribute]):
            filters += (not_(subclause),)
        else:
            raise Exception("%s - value must be truthy or falsey" % ('has_' + attribute))
    elif ('count_' + attribute) in params:
        primaryjoin = relation.property.primaryjoin
        value = params['count_' + attribute]
        count_clause = RelationshipCount(model, primaryjoin, value)
        if count_clause is not None:
            query = query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right).group_by(model).having(count_clause)
        else:
            raise Exception("%s - invalid value: %s" % ('count_' + attribute, value))
    if attribute in params:
        relation_model = RelationshipModel(model, attribute)
        aliased_model = aliased(relation_model)
        query = query.unique_join(aliased_model, relation)
        attr_filters, query = AllAttributeFilters(query, aliased_model, params[attribute])
        filters += (and_(*attr_filters),)
    return filters, query


# #### Type filter functions

def NumericFilters(model, columnname, params):
    type = ColumnType(model, columnname)

    def parser(value):
        nonlocal type
        return ParseCast(value, type)

    filters = ()
    if columnname in params:
        filters += (NumericMatching(model, columnname, params[columnname]),)
    if (columnname + '_not') in params:
        filters += (not_(NumericMatching(model, columnname, params[columnname + '_not'])),)
    if (columnname + '_eq') in params:
        filters += (getattr(model, columnname) == parser(params[columnname + '_eq']),)
    if (columnname + '_ne') in params:
        filters += (getattr(model, columnname) != parser(params[columnname + '_ne']),)
    if (columnname + '_gt') in params:
        filters += (getattr(model, columnname) > parser(params[columnname + '_gt']),)
    if (columnname + '_ge') in params:
        filters += (getattr(model, columnname) >= parser(params[columnname + '_ge']),)
    if (columnname + '_lt') in params:
        filters += (getattr(model, columnname) < parser(params[columnname + '_lt']),)
    if (columnname + '_le') in params:
        filters += (getattr(model, columnname) <= parser(params[columnname + '_le']),)
    return filters


def TextFilters(model, columnname, params):
    filters = ()
    if columnname in params:
        filters += (getattr(model, columnname) == params[columnname],)
    cmp_regex = re.compile(TEXT_COMPARISON_RE % columnname)
    cmp_matches = [cmp_regex.match(key) for key in params.keys()]
    cmp_types = [match.group(1) for match in cmp_matches if match is not None]
    print("TextFilters - compare types:", cmp_types)
    for cmp_type in cmp_types:
        param_key = columnname + '_' + cmp_type
        filters += (TextComparisonMatching(model, columnname, params[param_key], cmp_type),)
    if (columnname + '_exists') in params:
        filters += (TextExistenceMatching(model, columnname, params[columnname + '_exists']),)
    array_regex = re.compile(TEXT_ARRAY_RE % columnname)
    array_matches = [array_regex.match(key) for key in params.keys()]
    array_types = [match.group(1) for match in array_matches if match is not None]
    print("TextFilters - array types:", array_types)
    for array_type in array_types:
        param_key = columnname + '_' + array_type
        filters += (TextArrayMatching(model, columnname, params[param_key], array_type),)
    return filters


def BooleanFilters(model, columnname, params):
    if columnname in params:
        return BooleanMatching(model, columnname, params[columnname])
    return ()


# #### Type auxiliary functions

def RelationshipCount(model, primaryjoin, value):
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


def NumericMatching(model, columnname, value):
    type = ColumnType(model, columnname)

    def parser(value):
        nonlocal type
        return ParseCast(value, type)

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


def TextComparisonMatching(model, columnname, value, cmp_type):
    if cmp_type == 'eq':
        return getattr(model, columnname) == value
    if cmp_type == 'ne':
        return getattr(model, columnname) != value
    if cmp_type == 'like':
        return getattr(model, columnname).like(SQLEscape(value), escape='\x01')
    if cmp_type == 'ilike':
        return getattr(model, columnname).ilike(SQLEscape(value), escape='\x01')
    if cmp_type == 'not_like':
        return not_(getattr(model, columnname).like(SQLEscape(value), escape='\x01'))
    if cmp_type == 'not_ilike':
        return not_(getattr(model, columnname).ilike(SQLEscape(value), escape='\x01'))
    if cmp_type == 'regex':
        return getattr(model, columnname).regexp_match(value)
    if cmp_type == 'not_regex':
        return not_(getattr(model, columnname).regexp_match(value))


def TextExistenceMatching(model, columnname, value):
    if IsTruthy(value):
        return getattr(model, columnname).__ne__(None)
    elif IsFalsey(value):
        return getattr(model, columnname).__eq__(None)
    else:
        raise Exception("%s - value must be truthy or falsey" % (columnname + '_exists'))


def TextArrayMatching(model, columnname, value, array_type):
    print("TextArrayMatching", model, columnname, value, array_type)
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
        return sqlfuncs.lower(getattr(model, columnname)).in_(value_array)
    if array_type in NOT_ARRAY_TYPES and array_type in LOWER_ARRAY_TYPES:
        return not_(sqlfuncs.lower(getattr(model, columnname)).in_(value_array))


def BooleanMatching(model, columnname, value):
    if IsTruthy(value):
        return (getattr(model, columnname).__eq__(True),)
    if IsFalsey(value):
        return (getattr(model, columnname).__eq__(False),)
    raise Exception("%s - value must be truthy or falsey" % columnname)
