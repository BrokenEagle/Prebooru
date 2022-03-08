# APP/HELPERS/ARCHIVE_DATA_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

def reinstantiate_item_link(archive_data):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Recreate", url_for('archive_data.reinstantiate_item_html', id=archive_data.id), **addons)


def relink_item_link(archive_data):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Relink", url_for('archive_data.relink_item_html', id=archive_data.id), **addons)


def set_permenant_link(archive_data):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Unexpire", url_for('archive_data.set_permenant_html', id=archive_data.id), **addons)


def set_temporary_link(archive_data):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Expire", url_for('archive_data.set_temporary_html', id=archive_data.id), **addons)


def has_relink(archive_data):
    for key in archive_data.data['links']:
        if len(archive_data.data['links'][key]) > 0:
            return True
    return False
