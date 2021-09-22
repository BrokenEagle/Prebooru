# APP/DATABASE/SIMILARITY_DATA_DB.PY

# ##LOCAL IMPORTS
from .. import SESSION
from ..models import SimilarityData
from .base_db import update_column_attributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['post_id', 'ratio', 'image_hash']

CREATE_ALLOWED_ATTRIBUTES = ['post_id', 'ratio', 'image_hash']


# ##FUNCTIONS

# #### DB functions

# ###### CREATE

def create_similarity_data_from_parameters(createparams):
    similarity_data = SimilarityData()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(similarity_data, update_columns, createparams)
    print("[%s]: created" % similarity_data.shortlink)
    return similarity_data


# ###### DELETE

def delete_similarity_data_by_post_id(post_id):
    SimilarityData.query.filter(SimilarityData.post_id == post_id).delete()
    SESSION.commit()


# #### Misc functions

def get_similarity_data_by_post_id(post_id):
    return SimilarityData.query.filter(SimilarityData.post_id == post_id).all()
