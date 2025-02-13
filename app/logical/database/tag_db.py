# APP/LOGICAL/DATABASE/TAG_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import SiteTag, UserTag, IllustTags, PostTags
from .base_db import set_column_attributes, save_record, commit_session


# ## GLOBAL VARIABLES

TAG_UNION_CLAUSE = union_all(
    IllustTags.query.with_entities(IllustTags.tag_id),
    PostTags.query.with_entities(PostTags.tag_id),
)

ANY_WRITABLE_ATTRIBUTES = ['name']
NULL_WRITABLE_ATTRIBUTES = []

TAG_MODEL_DICT = {
    'site_tag': SiteTag,
    'user_tag': UserTag,
}


# ## FUNCTIONS

# #### Create

def create_tag_from_parameters(createparams, commit=True):
    tag = TAG_MODEL_DICT[createparams['type']]()
    return set_tag_from_parameters(tag, createparams, 'created', commit)


# #### Set

def set_tag_from_parameters(tag, setparams, action, commit):
    if set_column_attributes(tag, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(tag, action, commit=commit)
    return tag


# #### Delete

def prune_unused_tags():
    # Only site tags are automatically pruneable. User tags must be removed manually.
    delete_count = SiteTag.query.filter(SiteTag.id.not_in(TAG_UNION_CLAUSE))\
                                .delete(synchronize_session=False)
    commit_session()
    return delete_count
