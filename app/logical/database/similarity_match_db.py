# APP/LOGICAL/DATABASE/SIMILARITY_MATCH_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SimilarityMatch
from .base_db import update_column_attributes

# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['forward_id', 'reverse_id', 'score']

CREATE_ALLOWED_ATTRIBUTES = ['forward_id', 'reverse_id', 'score']
UPDATE_ALLOWED_ATTRIBUTES = ['score']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_similarity_match_from_parameters(createparams):
    similarity_match = SimilarityMatch()
    if createparams['forward_id'] > createparams['reverse_id']:
        createparams['forward_id'], createparams['reverse_id'] = createparams['reverse_id'], createparams['forward_id']
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(similarity_match, update_columns, createparams, commit=False)
    print("[%s]: created\n" % similarity_match.shortlink)
    return similarity_match


# ###### UPDATE

def update_similarity_match_from_parameters(similarity_match, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(similarity_match, update_columns, updateparams, commit=False))
    if any(update_results):
        print("[%s]: updated\n" % similarity_match.shortlink)


# ###### DELETE

def delete_similarity_match(similarity_match):
    SESSION.delete(similarity_match)
    SESSION.flush()


def batch_delete_similarity_matches(similarity_matches):
    for similarity_match in similarity_matches:
        SESSION.delete(similarity_match)
    SESSION.flush()


def delete_similarity_matches_by_post_id(post_id):
    SimilarityMatch.query.filter(_post_id_clause(post_id)).delete()
    SESSION.flush()


# ###### Query

def get_similarity_matches_by_post_id(post_id):
    return SimilarityMatch.query.filter(_post_id_clause(post_id)).all()


# #### Private

def _post_id_clause(post_id):
    return or_(SimilarityMatch.forward_id == post_id, SimilarityMatch.reverse_id == post_id)
