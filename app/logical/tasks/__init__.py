# APP/LOGICAL/TASKS/__INIT__.PY

"""For logic which is to be done on a schedule or asynchronously."""

# ## PACKAGE IMPORTS
from config import EXPUNGE_CACHE_RECORDS, EXPUNGE_ARCHIVE_RECORDS, GENERATE_MISSING_IMAGE_HASHES,\
    CALCULATE_SIMILARITY_MATCHES, CHECK_ALL_BOORUS, CHECK_ALL_ARTISTS_FOR_BOORUS,\
    CHECK_ALL_POSTS_FOR_DANBOORU_ID, CHECK_PENDING_SUBSCRIPTIONS, CHECK_PENDING_DOWNLOADS,\
    UNLINK_EXPIRED_SUBSCRIPTION_ELEMENTS, DELETE_EXPIRED_SUBSCRIPTION_ELEMENTS,\
    ARCHIVE_EXPIRED_SUBSCRIPTION_ELEMENTS, RECALCULATE_POOL_POSITIONS, RELOCATE_OLD_POSTS,\
    DELETE_ORPHAN_IMAGES, VACUUM_ANALYZE_DATABASE


# ## GLOBAL VARIABLES

# #### WORKER CONFIG

WORKER_LOCKS = ['process_subscription_manual']

# #### SCHEDULE_CONFIG

JOB_ITEMS = [{
    'name': 'expunge_cache_records',
    'config': EXPUNGE_CACHE_RECORDS,
    },{
    'name': 'expunge_archive_records',
    'config': EXPUNGE_ARCHIVE_RECORDS,
    },{
    'name': 'generate_missing_image_hashes',
    'config': GENERATE_MISSING_IMAGE_HASHES,
    },{
    'name': 'calculate_similarity_matches',
    'config': CALCULATE_SIMILARITY_MATCHES,
    },{
    'name': 'check_all_boorus',
    'config': CHECK_ALL_BOORUS,
    },{
    'name': 'check_all_artists_for_boorus',
    'config': CHECK_ALL_ARTISTS_FOR_BOORUS,
    },{
    'name': 'check_all_posts_for_danbooru_id',
    'config': CHECK_ALL_POSTS_FOR_DANBOORU_ID,
    },{
    'name': 'check_pending_subscriptions',
    'config': CHECK_PENDING_SUBSCRIPTIONS,
    },{
    'name': 'check_pending_downloads',
    'config': CHECK_PENDING_DOWNLOADS,
    },{
    'name': 'unlink_expired_subscription_elements',
    'config': UNLINK_EXPIRED_SUBSCRIPTION_ELEMENTS,
    },{
    'name': 'delete_expired_subscription_elements',
    'config': DELETE_EXPIRED_SUBSCRIPTION_ELEMENTS,
    },{
    'name': 'archive_expired_subscription_elements',
    'config': ARCHIVE_EXPIRED_SUBSCRIPTION_ELEMENTS,
    },{
    'name': 'recalculate_pool_positions',
    'config': RECALCULATE_POOL_POSITIONS,
    },{
    'name': 'relocate_old_posts',
    'config': RELOCATE_OLD_POSTS,
    },{
    'name': 'delete_orphan_images',
    'config': DELETE_ORPHAN_IMAGES,
    },{
    'name': 'vacuum_analyze_database',
    'config': VACUUM_ANALYZE_DATABASE,
}]

JOB_CONFIG = {
    item['name']: {
        'config': {
            'id': item['name'],
            item['config'][0]: item['config'][1],
            'jitter': item['config'][2],
        },
        'leeway': item['config'][3],
    }
    for item in JOB_ITEMS
}

# ## JOB DB VARIABLES

ALL_JOB_INFO = list(JOB_CONFIG.keys()) + ['heartbeat']
ALL_JOB_ENABLED = list(JOB_CONFIG.keys())
ALL_JOB_MANUAL = list(JOB_CONFIG.keys())
ALL_JOB_LOCKS = WORKER_LOCKS + list(JOB_CONFIG.keys())
ALL_JOB_TIMEVALS = list(JOB_CONFIG.keys())
