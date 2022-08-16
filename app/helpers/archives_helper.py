# APP/HELPERS/ARCHIVES_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

def reinstantiate_item_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Recreate", url_for('archive.reinstantiate_item_html', id=archive.id), **addons)


def relink_item_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Relink", url_for('archive.relink_item_html', id=archive.id), **addons)


def set_permenant_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Unexpire", url_for('archive.set_permenant_html', id=archive.id), **addons)


def set_temporary_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Expire", url_for('archive.set_temporary_html', id=archive.id), **addons)


def has_relink(archive):
    for key in archive.data['links']:
        if len(archive.data['links'][key]) > 0:
            return True
    return False
