# APP/LOGICAL/TASKS/__INIT__.PY

"""For logic which is to be done on a schedule or asynchronously."""

# WORKER CONFIG

WORKER_LOCKS = ['process_subscription']

# SCHEDULE_CONFIG

JOB_CONFIG = {
    'expunge_cache_records': {
        'config': {
            'id': 'expunge_cache_records',
            'hours': 8,
            'jitter': 3600,
        },
        'leeway': 300,
    },
    'expunge_archive_records': {
        'config': {
            'id': 'expunge_archive_records',
            'hours': 12,
            'jitter': 3600,
        },
        'leeway': 180,
    },
    'check_all_boorus': {
        'config': {
            'id': 'check_all_boorus',
            'days': 1,
            'jitter': 3600,
        },
        'leeway': 300,
    },
    'check_all_artists_for_boorus': {
        'config': {
            'id': 'check_all_artists_for_boorus',
            'days': 1,
            'jitter': 3600,
        },
        'leeway': 300,
    },
    'check_all_posts_for_danbooru_id': {
        'config': {
            'id': 'check_all_posts_for_danbooru_id',
            'days': 1,
            'jitter': 3600,
        },
        'leeway': 300,
    },
    'check_pending_subscriptions': {
        'config': {
            'id': 'check_pending_subscriptions',
            'hours': 1,
            'jitter': 300,
        },
        'leeway': 180,
    },
    'check_pending_downloads': {
        'config': {
            'id': 'check_pending_downloads',
            'hours': 1,
            'jitter': 300,
        },
        'leeway': 180,
    },
    'process_expired_subscription_elements': {
        'config': {
            'id': 'process_expired_subscription_elements',
            'hours': 4,
            'jitter': 1200,
        },
        'leeway': 300,
    },
    'relocate_old_posts': {
        'config': {
            'id': 'relocate_old_posts',
            'days': 1,
            'jitter': 3600,
        },
        'leeway': 300,
    },
    'delete_orphan_images': {
        'config': {
            'id': 'delete_orphan_images',
            'weeks': 1,
            'jitter': 3600,
        },
        'leeway': 300,
    },
    'vacuum_analyze_database': {
        'config': {
            'id': 'vacuum_analyze_database',
            'weeks': 1,
            'jitter': 3600,
        },
        'leeway': 300,
    },
}

# ## JOB DB VARIABLES

ALL_JOB_INFO = list(JOB_CONFIG.keys()) + ['heartbeat']
ALL_JOB_ENABLED = list(JOB_CONFIG.keys())
ALL_JOB_LOCKS = WORKER_LOCKS + list(JOB_CONFIG.keys())
ALL_JOB_TIMEVALS = list(JOB_CONFIG.keys())
