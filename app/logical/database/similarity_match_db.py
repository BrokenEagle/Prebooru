# APP/LOGICAL/DATABASE/SIMILARITY_MATCH_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## LOCAL IMPORTS
from ...models import SimilarityMatch
from .base_db import set_column_attributes, save_record, delete_record, commit_or_flush

# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['score']
NULL_WRITABLE_ATTRIBUTES = ['forward_id', 'reverse_id']


# ## FUNCTIONS

# #### Create

def create_similarity_match_from_parameters(createparams, commit=True):
    similarity_match = SimilarityMatch()
    if createparams['forward_id'] > createparams['reverse_id']:
        createparams['forward_id'], createparams['reverse_id'] = createparams['reverse_id'], createparams['forward_id']
    return set_similarity_match_from_parameters(similarity_match, createparams, 'created', commit)


# #### Update

def update_similarity_match_from_parameters(similarity_match, updateparams, commit=True):
    return set_similarity_match_from_parameters(similarity_match, updateparams, 'updated', commit)


# #### Set

def set_similarity_match_from_parameters(similarity_match, setparams, action, commit):
    if set_column_attributes(similarity_match, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(similarity_match, action, commit=commit)
    return similarity_match


# #### Delete

def delete_similarity_match(similarity_match, commit=False):
    delete_record(similarity_match)
    commit_or_flush(commit)


def batch_delete_similarity_matches(similarity_matches, commit=False):
    for similarity_match in similarity_matches:
        delete_record(similarity_match)
    commit_or_flush(commit)


def delete_similarity_matches_by_post_id(post_id, commit=False):
    SimilarityMatch.query.filter(_post_id_clause(post_id)).delete()
    commit_or_flush(commit)


# ###### Query

def get_similarity_matches_by_post_id(post_id):
    return SimilarityMatch.query.filter(_post_id_clause(post_id)).all()


# #### Private

def _post_id_clause(post_id):
    return or_(SimilarityMatch.forward_id == post_id, SimilarityMatch.reverse_id == post_id)
