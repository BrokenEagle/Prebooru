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
from ..logical.utility import eval_bool_string, merge_dicts
from ..logical.searchable import search_attributes


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


def referrer_check(endpoint, request):
    return urllib.parse.urlparse(request.referrer).path == url_for(endpoint)


def show_json(model, id, options=None):
    results = get_or_error(model, id, options)
    return results.to_json() if type(results) is not dict else results


def index_json(query, request):
    return jsonify([x.to_json() for x in paginate(query, request).items])


# #### Query helpers

def search_filter(query, search, negative_search=None):
    negative_search = negative_search if negative_search is not None else {}
    entity = _query_model(query)
    query = search_attributes(query, entity, search)
    if len(negative_search):
        negative_query = entity.query
        negative_query = search_attributes(negative_query, entity, negative_search)
        negative_query = negative_query.with_entities(entity.id)
        query = query.filter(not_(entity.id.in_(negative_query)))
    return query


def default_order(query, search):
    entity = query.column_descriptions[0]['entity']
    if 'order' in search:
        if search['order'] == 'custom':
            ids = [int(id) for id in search['id'].split(',') if id.isdigit()]
            if len(ids) > 1:
                return query.order_by(_custom_order(ids, entity))
        elif search['order'] == 'id_asc':
            return query.order_by(entity.id.asc())
    return query.order_by(entity.id.desc())


def paginate(query, request):
    return query.count_paginate(page=get_page(request), per_page=get_limit(request))


# #### ID helpers


def get_or_abort(model, id, options=None):
    options = options if options is not None else {}
    if len(options):
        item = model.query.options(*options).filter_by(id=id).first()
    else:
        item = model.find(id)
    if item is None:
        abort(404, "%s not found." % model.__name__)
    return item


def get_or_error(model, id, options=None):
    options = options if options is not None else {}
    if len(options):
        item = model.query.options(*options).filter_by(id=id).first()
    else:
        item = model.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % model.__name__}
    return item


# #### Form helpers


def hide_input(form, attr, value=None):
    field = getattr(form, attr)
    if value is not None:
        field.data = value
    field.widget = HiddenInput()
    field._value = lambda: field.data


# #### Param helpers


def get_page(request):
    return int(request.args['page']) if 'page' in request.args else 1


def get_limit(request):
    return int(request.args['limit']) if 'limit' in request.args else 20


def process_request_values(values_dict):
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
        merge_dicts(params, addhash)
    return params


def get_params_value(params, key, is_hash=False):
    default = {} if is_hash else None
    value = params.get(key, default)
    if is_hash and type(value) is not dict:
        value = default
    return value


def get_data_params(request, key):
    params = process_request_values(request.values)
    return get_params_value(params, key, True)


def set_error(retdata, message):
    retdata['error'] = True
    retdata['message'] = message
    return retdata


def parse_array_parameter(dataparams, array_key, string_key, separator):
    if array_key in dataparams and type(dataparams[array_key]) is list:
        return dataparams[array_key]
    if string_key in dataparams:
        return parse_string_list(dataparams, string_key, separator)


def parse_bool_parameter(dataparams, bool_key):
    return eval_bool_string(dataparams[bool_key]) if bool_key in dataparams else None


def parse_string_list(params, key, separator):
    return [item.strip() for item in re.split(separator, params[key]) if item.strip() != ""]


def parse_item(value, parser):
    try:
        return parser(value)
    except Exception:
        return None


def parse_type(params, key, parser):
    try:
        return parse_item(params[key], parser)
    except Exception:
        return None


def parse_list_type(params, key, parser):
    if key not in params or type(params[key]) is not list:
        return None
    return [subitem for subitem in [parse_item(item, parser) for item in params[key]] if subitem is not None]


def check_param_requirements(params, requirements):
    return reduce(lambda acc, x: acc + (["%s not present or invalid." % x] if params[x] is None else []), requirements, [])


def int_or_blank(data):
    try:
        return int(data)
    except Exception:
        return ""


def nullify_blanks(data):
    def _Check(val):
        return type(val) is str and val.strip() == ""
    return {k: (v if not _Check(v) else None) for (k, v) in data.items()}


def set_default(indict, key, default):
    indict[key] = indict[key] if (key in indict and indict[key] is not None) else default


def build_url_args(params, permit_list):  # Unused
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

def _custom_order(ids, entity):
    return case(
        {id: index for index, id in enumerate(ids)},
        value=entity.id,
    )


def _query_model(query):
    return query.column_descriptions[0]['entity']
