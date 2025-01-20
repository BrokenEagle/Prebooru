# APP/LOGICAL/DATABASE/DESCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import Description, Illust, IllustTitles, IllustCommentaries, AdditionalCommentaries, ArtistProfiles
from .base_db import commit_session


# ## GLOBAL VARIABLES

DESCRIPTION_UNION_CLAUSE = union_all(
    Illust.query.filter(Illust.title_id.is_not(None)).with_entities(Illust.title_id),
    Illust.query.filter(Illust.commentary_id.is_not(None)).with_entities(Illust.commentary_id),
    IllustTitles.query.with_entities(IllustTitles.description_id),
    IllustCommentaries.query.with_entities(IllustCommentaries.description_id),
    AdditionalCommentaries.query.with_entities(AdditionalCommentaries.description_id),
    ArtistProfiles.query.with_entities(ArtistProfiles.description_id)
)


# ## FUNCTIONS

# #### Delete

def prune_unused_descriptions():
    delete_count = Description.query.filter(Description.id.not_in(DESCRIPTION_UNION_CLAUSE))\
                                    .delete(synchronize_session=False)
    commit_session()
    return delete_count
