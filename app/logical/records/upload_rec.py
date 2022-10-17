# APP/LOGICAL/RECORDS/UPLOAD_REC.PY

# ## PACKAGE IMPORTS
from utility.data import add_dict_entry

# ## LOCAL IMPORTS
from ..sources.base import get_post_source
from ..database.illust_db import get_site_illust, get_site_illusts
from ..database.upload_element_db import create_upload_element_from_parameters


# ## FUNCTIONS

def populate_upload_elements(upload, illust=None):
    if illust is None:
        source = get_post_source(upload.request_url)
        site_illust_id = source.get_illust_id(upload.request_url)
        site_id = source.SITE_ID
        illust = get_site_illust(site_illust_id, site_id)
        if illust is None:
            return
    else:
        source = illust._source
    all_upload_urls = [source.normalize_image_url(upload_url.url) for upload_url in upload.image_urls]
    upload_elements = list(upload.elements)
    for illust_url in illust.urls:
        if (len(all_upload_urls) > 0) and (illust_url.url not in all_upload_urls):
            continue
        element = next((element for element in upload_elements if element.illust_url_id == illust_url.id), None)
        if element is None:
            element = create_upload_element_from_parameters({'upload_id': upload.id, 'illust_url_id': illust_url.id}, commit=False)
            upload_elements.append(element)
    return upload_elements


def populate_all_upload_elements(uploads):
    illust_lookup = {}
    illust_index = {}
    upload_elements = {}
    for upload in uploads:
        source = get_post_source(upload.request_url)
        site_illust_id = source.get_illust_id(upload.request_url)
        site_id = source.SITE_ID
        add_dict_entry(illust_lookup, site_id, site_illust_id)
        illust_index[upload.id] = {'site_id': site_id, 'site_illust_id': site_illust_id}
    illusts = []
    for key in illust_lookup:
        illusts += get_site_illusts(key, illust_lookup[key], load_urls=True)
    for upload in uploads:
        illust_params = illust_index[upload.id]
        illust = next((illust for illust in illusts
                       if illust.site_id == illust_params['site_id']
                       and illust.site_illust_id == illust_params['site_illust_id']), None)
        if illust is None:
            continue
        upload_elements[upload.id] = populate_upload_elements(upload, illust=illust)
    return upload_elements
