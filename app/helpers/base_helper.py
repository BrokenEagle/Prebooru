# APP/HELPERS/BASE_HELPER.PY

# ## PYTHON IMPORTS
import re
import html
import datetime

# ## EXTERNAL IMPORTS
from flask import Markup, request, url_for
from wtforms import Field, BooleanField
from wtforms.widgets import HiddenInput

# ## PACKAGE IMPORTS
from utility.time import time_ago

# ## LOCAL IMPORTS
from ..logical.sources import pixiv, twitter


# ## GLOBAL VARIABLES

HTTP_RG = re.compile(r'(\b(?:http|https)(?::\/{2}[\w]+)(?:[\/|\.]?)(?:[^\s<>\uff08\uff09\u3011\u3000"\[\]]*))',
                     re.IGNORECASE | re.ASCII)
LOCAL_SHORTLINK_RG = re.compile(r'\b(booru|artist|illust|post|upload|pool|notation) #(\d+)\b', re.IGNORECASE)
SITE_SHORTLINK_RG = re.compile(r'\b(pixiv|pxuser|twitter|twuser) #(\d+)\b', re.IGNORECASE)

SITE_URL_DICT = {
    'pixiv': pixiv.ILLUST_HREFURL,
    'pxuser': pixiv.ARTIST_HREFURL,
    'twitter': twitter.ILLUST_HREFURL,
    'twuser': twitter.ARTIST_HREFURL,
}


# ## FUNCTIONS

# #### Format functions

def html_kebab_case(text):
    return text.lower().replace(" ", "-").replace("&raquo;", "").strip("-")


def val_or_none(val):
    return Markup('<em>none</em>') if val is None else val


def format_timestamp(timeval):
    return datetime.datetime.isoformat(timeval) if timeval is not None else Markup('<em>N/A</em>')


def format_timestamp_difference(item):
    text = format_timestamp(item.created)
    delta = item.updated - item.created
    if delta.days > 0 or delta.seconds > 3600:
        text += " ( %s )" % time_ago(item.updated)
    return text


def convert_to_html(text):
    links = HTTP_RG.findall(text)
    output_html = html.escape(text)
    for link in links:
        escaped_link = re.escape(html.escape(link))
        link_match = re.search(escaped_link, output_html)
        if link_match is None:
            continue
        html_link = url_link(link)
        output_html = output_html[:link_match.start()] + str(html_link) + output_html[link_match.end():]
    output_html = _convert_local_short_links(output_html)
    output_html = _convert_site_short_links(output_html)
    output_html = re.sub(r'\r?\n', '<br>', output_html)
    return Markup(output_html)


# #### HTML functions

def add_container(tagname, markup_text, classlist=[], **attrs):
    class_string = ' class="%s"' % ' '.join(classlist) if len(classlist) > 0 else ''
    attr_string = ' ' + ' '.join(['%s="%s"' % attr for attr in attrs.items()]) if len(attrs) else ''
    return Markup('<%s%s%s>' % (tagname, class_string, attr_string)) + markup_text + Markup('</%s>' % tagname)


def external_link(text, url, **addons):
    addons['rel'] = addons['rel'] if 'rel' in addons else ""
    addons['rel'] = ' '.join((addons['rel'].split() + ['external', 'noreferrer', 'nofollow']))
    addons['target'] = '_blank'
    return general_link(text, url, **addons)


def general_link(text, url, method=None, **addons):
    if text is None or url is None:
        return Markup('<em>none</em>')
    if method == "POST":
        addons['onclick'] = "return Prebooru.linkPost(this)"
    elif method == "DELETE":
        addons['onclick'] = "return Prebooru.deleteConfirm(this)"
    attrs = ['%s="%s"' % (k, v) for (k, v) in addons.items()]
    return Markup('<a %s href="%s">%s</a>' % (' '.join(attrs), url, text))


def show_link(model_type, model_id):
    """Generate show link without having to load a relationship"""
    return general_link("%s #%d" % (model_type, model_id), url_for(model_type + '.show_html', id=model_id))


def url_link(url):
    return external_link(url, url)


def page_link(text, endpoint, page):
    return general_link(text, url_for_with_params(endpoint, page=page))


def file_link(file_path, link_text=None):
    addons = {'onclick': 'return Prebooru.copyFileLink(this)', 'data-file-path': file_path}
    link_text = file_path if link_text is None else link_text
    return general_link(link_text, "javascript:void(0)", **addons)


# #### Form functions

def form_iterator(form):
    """Yield the field name and a callable function given the order of fields in the form class"""
    # Get the names of all of the form fields
    form_fields = [attr for attr in dir(form) if _is_field(form, attr)]
    for field in form:
        # Get the current field name
        field_name = next(filter(lambda x: getattr(form, x) == field, form_fields))

        def _builder(**kwargs):
            nonlocal field
            if type(field) is BooleanField:
                # Add a hidden field to get the value of 0 when the boolean field is not set
                built_markup = str(field.label) + field(value="1") + field(value="0", type="hidden")
            elif type(field.widget) is HiddenInput:
                # Hide inputs marked as hidden in the controller if they have data
                classlist = ['input', 'hidden']
                return add_container('div', str(field), classlist=classlist) if field.data is not None else ""
            else:
                built_markup = str(field.label)
                if 'onclick' in kwargs:
                    # Supports selection inputs that change the form depending on the value
                    built_markup += field(onclick=kwargs['onclick'])
                else:
                    built_markup += field
            description = kwargs['description'] if 'description' in kwargs else field.description
            if description:
                # Add description if set in class definition or on template form
                built_markup += add_container('span', description, classlist=['description'])
            # Allow classes to be set individually for any input
            classlist = ['input'] + (kwargs['classlist'] if 'classlist' in kwargs else [])
            return add_container('div', built_markup, classlist=classlist)

        yield field_name, _builder


# #### URL functions

def search_url_for(endpoint, **kwargs):
    """Construct search URL for any endpoint given a dict of search parameters"""
    def _recurse(current_key, arg_dict, url_args):
        for key in arg_dict:
            updated_key = current_key + '[' + key + ']'
            if type(arg_dict[key]) is dict:
                _recurse(updated_key, arg_dict[key], url_args)
            else:
                url_args[updated_key] = arg_dict[key]
    url_args = {}
    _recurse('search', kwargs, url_args)
    return url_for(endpoint, **url_args)


def url_for_with_params(endpoint, **kwargs):
    """Construct URL given the current URL parameters"""
    url_args = {}
    for arg in kwargs:
        url_args[arg] = kwargs[arg]
    for arg in (k for k in request.args if k not in kwargs):
        url_args[arg] = request.args[arg]
    if request.endpoint.find('.show_html') >= 0:
        url_args['id'] = int(re.search(r'\d+$', request.path).group(0))
    return url_for(endpoint, **url_args)


# #### Navigation functions

def nav_link_to(text, endpoint):
    link_blueprint = endpoint.split('.')[0]
    request_blueprint = request.endpoint.split('.')[0]
    klass = 'current' if link_blueprint == request_blueprint else None
    html_text = html_kebab_case(text)
    return html_text, klass


def subnav_link_to(text, attrs):
    html_text = html_kebab_case(text)
    attrs['id'] = "subnav-" + html_text + "-link"
    return html_text, attrs


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


def break_period(text):
    return Markup(text.replace('.', '.<wbr>'))


# #### Private functions

def _is_field(form, attr):
    return not attr.startswith('__') and issubclass(getattr(form, attr).__class__, Field)


def _convert_local_short_links(text):
    position = 0
    while True:
        match = LOCAL_SHORTLINK_RG.search(text, pos=position)
        if not match:
            return text
        link_url = url_for(match.group(1) + '.show_html', id=int(match.group(2)))
        link = str(general_link(match.group(0), link_url))
        text = text[:match.start()] + link + text[match.end():]
        position = match.start() + len(link)


def _convert_site_short_links(text):
    position = 0
    while True:
        match = SITE_SHORTLINK_RG.search(text, pos=position)
        if not match:
            return text
        format_str = SITE_URL_DICT[match.group(1)]
        link_url = format_str % int(match.group(2))
        link = str(external_link(match.group(0), link_url))
        text = text[:match.start()] + link + text[match.end():]
        position = match.start() + len(link)
