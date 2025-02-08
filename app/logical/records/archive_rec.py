# APP/LOGICAL/RECORDS/ARCHIVE_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.file import delete_file
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Archive, ArchivePost, ArchiveIllust, ArchiveArtist, ArchiveBooru
from ..database.base_db import commit_session


# ## FUNCTIONS

def delete_expired_archives():
    status = {}
    expired = Archive.query.filter(Archive.expires < get_current_time())\
                           .with_entities(Archive.id)\
                           .all()
    expired_ids = list(itertools.chain(*expired))
    archive_posts = ArchivePost.query.filter(ArchivePost.archive_id.in_(expired_ids)).all()
    for archive_post in archive_posts:
        delete_file(archive_post.file_path)
        if archive_post.has_preview:
            delete_file(archive_post.preview_path)
    status['posts'] = ArchivePost.query.filter(ArchivePost.archive_id.in_(expired_ids)).delete()
    status['illusts'] = ArchiveIllust.query.filter(ArchiveIllust.archive_id.in_(expired_ids)).delete()
    status['artists'] = ArchiveArtist.query.filter(ArchiveArtist.archive_id.in_(expired_ids)).delete()
    status['boorus'] = ArchiveBooru.query.filter(ArchiveBooru.archive_id.in_(expired_ids)).delete()
    status['total'] = Archive.query.filter(Archive.id.in_(expired_ids)).delete()
    commit_session()
    return status
