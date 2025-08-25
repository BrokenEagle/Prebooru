# APP/LOGICAL/DATABASE/DESCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all

# ## LOCAL IMPORTS
from ...models import Description, Artist, Illust, IllustTitles, IllustCommentaries, AdditionalCommentaries,\
    ArtistProfiles
from .base_db import remove_duplicate_items, prune_unused_items


# ## GLOBAL VARIABLES

DESCRIPTION_UNION_CLAUSE = union_all(
    Illust.query.filter(Illust.title_id.is_not(None)).with_entities(Illust.title_id),
    Illust.query.filter(Illust.commentary_id.is_not(None)).with_entities(Illust.commentary_id),
    IllustTitles.query.with_entities(IllustTitles.description_id),
    IllustCommentaries.query.with_entities(IllustCommentaries.description_id),
    AdditionalCommentaries.query.with_entities(AdditionalCommentaries.description_id),
    Artist.query.filter(Artist.profile_id.is_not(None)).with_entities(Artist.profile_id),
    ArtistProfiles.query.with_entities(ArtistProfiles.description_id)
)

DESCRIPTION_FOREIGN_KEYS = [
    (Illust, Illust.title_id),
    (Illust, Illust.commentary_id),
    (IllustTitles, IllustTitles.description_id, 'illust_id'),
    (IllustCommentaries, IllustCommentaries.description_id, 'illust_id'),
    (AdditionalCommentaries, AdditionalCommentaries.description_id, 'illust_id'),
    (Artist, Artist.profile_id),
    (ArtistProfiles, ArtistProfiles.description_id, 'artist_id'),
]


# ## FUNCTIONS

def remove_duplicate_descriptions():
    return remove_duplicate_items(Description, Description.body, DESCRIPTION_FOREIGN_KEYS)


def prune_unused_descriptions():
    return prune_unused_items(Description, DESCRIPTION_UNION_CLAUSE)
