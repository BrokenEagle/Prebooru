# APP/HELPERS/ILLUSTS_HELPERS.PY

# ##PYTHON IMPORTS
import re
import html
import datetime
from flask import Markup, request, render_template, url_for
from wtforms import Field, BooleanField
from wtforms.widgets import HiddenInput

# ##LOCAL IMPORTS
from ..logical.utility import time_ago


# ##FUNCTIONS

# #### Format functions

def str_or_none(val):
    return Markup('<em>none</em>') if val is None else val


def format_timestamp(timeval):
    return datetime.datetime.isoformat(timeval) if timeval is not None else Markup('<em>none</em>')


def format_timestamps(item):
    text = format_timestamp(item.created)
    delta = item.updated - item.created
    if delta.days > 0 or delta.seconds > 3600:
        text += " ( %s )" % time_ago(item.updated)
    return text


# #### HTML functions

def convert_str_to_html(text):
    return Markup(re.sub('\r?\n', '<br>', html.escape(text)))


def description_text(description):
    return Markup('<span class="description">' + description + '</span>')


def add_container(tagname, markup_text, classlist=[], **attrs):
    class_string = ' class="%s"' % ' '.join(classlist) if len(classlist) > 0 else ''
    attr_string = ' ' + ' '.join(['%s="%s"' % attr for attr in attrs.items()]) if len(attrs) else ''
    return Markup('<%s%s%s>' % (tagname, class_string, attr_string)) + markup_text + Markup('</%s>' % tagname)


def external_link(text, url, **addons):
    addons['rel'] = addons['rel'] if 'rel' in addons else ""
    addons['rel'] = ' '.join((addons['rel'].split() + ['external', 'noreferrer', 'nofollow']))
    addons['target'] = '_blank'
    return general_link(text, url, **addons)


def general_link(text, url, **addons):
    attrs = ['%s="%s"' % (k, v) for (k, v) in addons.items()]
    return Markup('<a %s href="%s">%s</a>' % (' '.join(attrs), url, text))


def show_link(model_type, model_id):
    return general_link("%s #%d" % (model_type, model_id), url_for(model_type + '.show_html', id=model_id))


def url_link(url):
    return external_link(url, url)


# #### Form functions

def form_iterator(form):
    form_fields = [attr for attr in dir(form) if not attr.startswith('__') and issubclass(getattr(form, attr).__class__, Field)]
    for field in form:
        field_name = next(filter(lambda x: getattr(form, x) == field, form_fields))

        def _builder(**kwargs):
            nonlocal field
            if type(field) is BooleanField:
                built_markup = str(field.label) + field(value="1") + field(value="0", type="hidden")
            elif type(field.widget) is HiddenInput:
                return add_container('div', str(field), classlist=['input', 'hidden']) if field.data is not None else ""
            else:
                built_markup = str(field.label)
                if 'onclick' in kwargs:
                    built_markup += field(onclick=kwargs['onclick'])
                else:
                    built_markup += field
            description = kwargs['description'] if 'description' in kwargs else field.description
            if description:
                built_markup += description_text(description)
            classlist = ['input'] + (kwargs['classlist'] if 'classlist' in kwargs else [])
            return add_container('div', built_markup, classlist=classlist)

        yield field_name, _builder


# #### URL functions

def search_url_for(endpoint, **kwargs):
    def _Recurse(current_key, arg_dict, url_args):
        for key in arg_dict:
            updated_key = current_key + '[' + key + ']'
            if type(arg_dict[key]) is dict:
                _Recurse(updated_key, arg_dict[key], url_args)
            else:
                url_args[updated_key] = arg_dict[key]
    url_args = {}
    _Recurse('search', kwargs, url_args)
    return url_for(endpoint, **url_args)


def url_for_with_args(endpoint, **kwargs):
    url_args = {}
    for arg in kwargs:
        url_args[arg] = kwargs[arg]
    for arg in request.args:
        if arg not in kwargs:
            url_args[arg] = request.args[arg]
    if request.endpoint.find('.show_html') >= 0:
        url_args['id'] = int(re.search(r'\d+$', request.path).group(0))
    return url_for(endpoint, **url_args)


# #### Navigation functions

def nav_link_to(text, endpoint):
    link_blueprint = endpoint.split('.')[0]
    request_blueprint = request.endpoint.split('.')[0]
    klass = 'current' if link_blueprint == request_blueprint else None
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_nav_link.html", text=text, html_text=html_text, endpoint=endpoint, klass=klass))


def subnav_link_to(text, endpoint, id=None, attrs=None, **kwargs):
    attrs = attrs if attrs is not None else {}
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_subnav_link.html", text=text, html_text=html_text, endpoint=endpoint, id=id, attrs=attrs, kwargs=kwargs))


def page_navigation(paginate):
    current_page = paginate.page
    previous_page = paginate.prev_num
    next_page = paginate.next_num
    last_page = paginate.pages
    left = max(current_page - 4, 2)
    penultimate_page = last_page - 1
    right = min(current_page + 4, penultimate_page)
    pages = [1]
    pages += ['...'] if left != 2 else []
    pages += list(range(left, right + 1))
    pages += ['...'] if right != penultimate_page else []
    pages += [last_page] if last_page > 1 else []
    return previous_page, current_page, next_page, pages


# #### Misc functions

def endpoint_classes(request):
    controller, action = [item.replace('_', '-') for item in request.endpoint.split('.')]
    controller = 'c-' + controller
    action = 'a-' + action.replace('-html', "")
    return controller + ' ' + action


def has_error_messages(messages):
    return any((category, message) for (category, message) in messages if category == 'error')
