# FIXES/022_SET_STATUS_ON_DUPLICATE_ERROR_SUBSCRIPTION_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys
import itertools


# ## FUNCTIONS

# #### Auxiliary functions

def initialize():
    global SESSION, SubscriptionElement, SubscriptionElementStatus, SubscriptionElementKeep
    os.environ['USE_ENUMS'] = 'false'
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import SubscriptionElement, SubscriptionElementStatus, SubscriptionElementKeep


# #### Main execution functions

def main():
    initialize()
    status_results =\
        SubscriptionElementStatus.query.filter(SubscriptionElementStatus.name.in_(('duplicate', 'error')))\
                                       .with_entities(SubscriptionElementStatus.id).all()
    status_ids = tuple(x for x in itertools.chain(*status_results))
    rows_updated =\
        SubscriptionElement.query.filter(SubscriptionElement.status_id.in_(status_ids))\
                           .update({'keep_id': SubscriptionElementKeep.unknown.id, 'expires': None})
    SESSION.commit()
    print("Rows updated:", rows_updated)


# ##EXECUTION START

if __name__ == '__main__':
    main()
