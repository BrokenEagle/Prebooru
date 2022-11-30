# FIXES/019_REMOVE_DUPLICATE_POOL_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global SESSION, PoolElement
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import PoolElement


def main():
    element_type_switcher = {
        'pool_post': lambda: ('post_id', 'posts'),
        'pool_illust': lambda: ('illust_id', 'illusts'),
        'pool_notation': lambda: ('notation_id', 'notations'),
    }
    initialize()
    pool_element_index = {}
    q = PoolElement.query
    page = q.count_paginate(per_page=200)
    while True:
        print(f"\nremove_duplicate_pool_elements: {page.first} - {page.last} / Total({page.count})\n")
        if len(page.items) == 0:
            break
        for element in page.items:
            if element.pool_id not in pool_element_index:
                pool_element_index[element.pool_id] = {
                    'posts': set(),
                    'illusts': set(),
                    'notations': set(),
                }
            pool_index = pool_element_index[element.pool_id]
            element_key, index_key = element_type_switcher[element.type.name]()
            item_id = getattr(element, element_key)
            item_set = pool_index[index_key]
            if item_id in item_set:
                print("Duplicate found:", element)
                SESSION.delete(element)
            else:
                item_set.add(item_id)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()
    print('\n')


# ##EXECUTION START

if __name__ == '__main__':
    main()
