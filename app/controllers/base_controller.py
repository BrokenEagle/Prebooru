# APP\CONTROLLERS\BASE_CONTROLLER.PY

# ## PYTHON IMPORTS
import re
import urllib
from functools import reduce
from flask import jsonify, abort, url_for
from sqlalchemy import not_
from sqlalchemy.sql.expression import case
from wtforms import Form
from wtforms.meta import DefaultMeta
from wtforms.widgets import HiddenInput

# ## LOCAL IMPORTS
from ..logical.utility import EvalBoolString, MergeDicts
from ..logical.searchable import SearchAttributes


# ## GLOBAL VARIABLES

# #### Classes


class BindNameMeta(DefaultMeta):
    def bind_field(self, form, unbound_field, options):
        if 'custom_name' in unbound_field.kwargs:
            options['name'] = unbound_field.kwargs.pop('custom_name')
        return unbound_field.bind(form=form, **options)


class CustomNameForm(Form):
    Meta = BindNameMeta


# ## FUNCTIONS


# #### Route helpers


def ReferrerCheck(endpoint, request):
    return urllib.parse.urlparse(request.referrer).path == url_for(endpoint)


def ShowJson(model, id, options=None):
    results = GetOrError(model, id, options)
    return results.to_json() if type(results) is not dict else results


def IndexJson(query, request):
    return jsonify([x.to_json() for x in Paginate(query, request).items])


# #### Query helpers

def SearchFilter(query, search, negative_search=None):
    negative_search = negative_search if negative_search is not None else {}
    entity = _QueryModel(query)
    query = SearchAttributes(query, entity, search)
    if len(negative_search):
        negative_query = entity.query
        negative_query = SearchAttributes(negative_query, entity, negative_search)
        negative_query = negative_query.with_entities(entity.id)
        query = query.filter(not_(entity.id.in_(negative_query)))
    return query


def DefaultOrder(query, search):
    entity = query.column_descriptions[0]['entity']
    if 'order' in search:
        if search['order'] == 'custom':
            ids = [int(id) for id in search['id'].split(',') if id.isdigit()]
            if len(ids) > 1:
                return query.order_by(_CustomOrder(ids, entity))
        elif search['order'] == 'id_asc':
            return query.order_by(entity.id.asc())
    return query.order_by(entity.id.desc())


def Paginate(query, request):
    return query.count_paginate(page=GetPage(request), per_page=GetLimit(request))


# #### ID helpers


def GetOrAbort(model, id, options=None):
    options = options if options is not None else {}
    if len(options):
        item = model.query.options(*options).filter_by(id=id).first()
    else:
        item = model.find(id)
    if item is None:
        abort(404, "%s not found." % model.__name__)
    return item


def GetOrError(model, id, options=None):
    options = options if options is not None else {}
    if len(options):
        item = model.query.options(*options).filter_by(id=id).first()
    else:
        item = model.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % model.__name__}
    return item


# #### Form helpers


def HideInput(form, attr, value=None):
    field = getattr(form, attr)
    if value is not None:
        field.data = value
    field.widget = HiddenInput()
    field._value = lambda: field.data


# #### Param helpers


def GetPage(request):
    return int(request.args['page']) if 'page' in request.args else 1


def GetLimit(request):
    return int(request.args['limit']) if 'limit' in request.args else 20


def ProcessRequestValues(values_dict):
    """
    Parse incomming URL parameters into a hash based upon a standard tokenizing scheme.

    Example:    firsttoken[secondtoken][thirdtoken][nthtoken]=value
    Equates to: {"firsttoken": {"secondtoken": {"thirdtoken": { "nthtoken": value}}}}

    Array values are indicated when the end of the token key is []

    Example:    firsttoken[]=value1&firsttoken[]=value2
    Equates to: {"firsttoken": [value1, value2]}
    """
    params = {}
    for key in values_dict:
        firstpos = key.find('[')
        if firstpos < 0:
            params[key] = values_dict.get(key)
            continue
        firsttoken = key[:firstpos]
        subsequenthashes = key[firstpos:]
        subsequenttokens = re.findall(r'\[([^]]*)\]', subsequenthashes)
        if any(token.find('[') >= 0 for token in subsequenttokens):  # Tokens cannot contain '['
            continue
        if any(token == '' for token in subsequenttokens[:-1]):  # Only the last token can be ""
            continue
        value = values_dict.getlist(key) if subsequenttokens[-1] == "" else values_dict.get(key)
        alltokens = [firsttoken] + (subsequenttokens[:-1] if subsequenttokens[-1] == "" else subsequenttokens)
        currenthash = addhash = {}
        for i in range(0, len(alltokens) - 1):
            token = alltokens[i]
            currenthash[token] = {}
            currenthash = currenthash[token]
        finaltoken = alltokens[-1]
        currenthash[finaltoken] = value
        MergeDicts(params, addhash)
    return params


def GetParamsValue(params, key, is_hash=False):
    default = {} if is_hash else None
    value = params.get(key, default)
    if is_hash and type(value) is not dict:
        value = default
    return value


def GetDataParams(request, key):
    params = ProcessRequestValues(request.values)
    return GetParamsValue(params, key, True)


def SetError(retdata, message):
    retdata['error'] = True
    retdata['message'] = message
    return retdata


def ParseArrayParameter(dataparams, array_key, string_key, separator):
    if array_key in dataparams and type(dataparams[array_key]) is list:
        return dataparams[array_key]
    if string_key in dataparams:
        return ParseStringList(dataparams, string_key, separator)


def ParseBoolParameter(dataparams, bool_key):
    return EvalBoolString(dataparams[bool_key]) if bool_key in dataparams else None


def ParseStringList(params, key, separator):
    return [item.strip() for item in re.split(separator, params[key]) if item.strip() != ""]


def ParseItem(value, parser):
    try:
        return parser(value)
    except Exception:
        return None


def ParseType(params, key, parser):
    try:
        return ParseItem(params[key], parser)
    except Exception:
        return None


def ParseListType(params, key, parser):
    if key not in params or type(params[key]) is not list:
        return None
    return [subitem for subitem in [ParseItem(item, parser) for item in params[key]] if subitem is not None]


def CheckParamRequirements(params, requirements):
    return reduce(lambda acc, x: acc + (["%s not present or invalid." % x] if params[x] is None else []), requirements, [])


def IntOrBlank(data):
    try:
        return int(data)
    except Exception:
        return ""


def NullifyBlanks(data):
    def _Check(val):
        return type(val) is str and val.strip() == ""
    return {k: (v if not _Check(v) else None) for (k, v) in data.items()}


def SetDefault(indict, key, default):
    indict[key] = indict[key] if (key in indict and indict[key] is not None) else default


def BuildUrlArgs(params, permit_list):
    urlparams = []
    for key, value in params.items():
        if key not in permit_list:
            continue
        if type(value) is list:
            for item in value:
                urlparams.append(urllib.parse.urlencode({key + '[]': item}))
        elif value is not None:
            urlparams.append(urllib.parse.urlencode({key: value}))
    return '&'.join(urlparams)


# #### Private functions

def _CustomOrder(ids, entity):
    return case(
        {id: index for index, id in enumerate(ids)},
        value=entity.id,
    )


def _QueryModel(query):
    return query.column_descriptions[0]['entity']
