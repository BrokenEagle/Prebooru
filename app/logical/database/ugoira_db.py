# APP/LOGICAL/DATABASE/UGOIRA_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import union_all, func

# ## LOCAL IMPORTS
from ...models import Ugoira, Post, IllustUrl
from .base_db import commit_session, flush_session, delete_record


# ## GLOBAL VARIABLES

UGOIRA_UNION_CLAUSE = union_all(
    Post.query.filter(Post.ugoira_id.is_not(None)).with_entities(Post.ugoira_id),
    IllustUrl.query.filter(IllustUrl.ugoira_id.is_not(None)).with_entities(IllustUrl.ugoira_id),
)

UGOIRA_FOREIGN_KEYS = [
    (Post, Post.ugoira_id),
    (IllustUrl, IllustUrl.ugoira_id),
]


# ## FUNCTIONS

def remove_duplicate_ugoiras():
    duplicates = Ugoira.query.group_by(Ugoira.frames)\
                             .having(func.count(Ugoira.frames) > 1)\
                             .with_entities(Ugoira.frames)\
                             .all()
    total = len(duplicates)
    if total == 0:
        return total
    for duplicate in duplicates:
        ugoiras = Ugoira.query.filter_by(frames=duplicate[0]).all()
        update_id = ugoiras[0].id
        # Remove duplicates in M2M beore updating, otherwise it could violate the unique constraint
        for foreign_key in UGOIRA_FOREIGN_KEYS:
            if not foreign_key[0]._secondary_table:
                continue
            model, attach_column, primary_id = foreign_key
            attach_id = attach_column.name
            primary_column = getattr(model, primary_id)
            items = model.query.filter(attach_column.in_(ugoira.id for ugoira in ugoiras)).all()
            seen_primary_ids = set()
            for item in items:
                if item[primary_id] in seen_primary_ids:
                    model.query.filter(primary_column == item[primary_id], attach_column == item[attach_id]).delete()
                    flush_session()
                else:
                    seen_primary_ids.add(item[primary_id])
        # Update tables to the first ugoira found
        for ugoira in ugoiras[1:]:
            for foreign_key in UGOIRA_FOREIGN_KEYS:
                model, attach_column, *_ = foreign_key
                model.query.filter(attach_column == ugoira.id).update({attach_column.name: update_id})
                flush_session()
            delete_record(ugoira)
            flush_session()
    commit_session()
    return total


def prune_unused_ugoiras():
    delete_count = Ugoira.query.filter(Ugoira.id.not_in(UGOIRA_UNION_CLAUSE))\
                               .delete(synchronize_session=False)
    commit_session()
    return delete_count
