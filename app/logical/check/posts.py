# APP/LOGICAL/CHECK/POSTS.PY

# ## PACKAGE IMPORTS
from utility.data import get_buffer_checksum
from utility.file import put_get_raw

# ## LOCAL IMPORTS
from ...models import Post
from ..searchable import search_attributes
from ..database.post_db import update_post_from_parameters
from ..sources.danbooru import get_posts_by_md5s
from ..downloader.network import redownload_post


# ## FUNCTIONS

def check_all_posts_for_danbooru_id():
    print("Checking all posts for Danbooru ID.")
    query = Post.query.filter(Post.danbooru_id.is_(None))
    query = search_attributes(query, Post, {'subscription_element_exists': 'false'})
    max_id = 0
    page = 1
    page_count = (query.get_count() // 100) + 1
    while True:
        posts = query.filter(Post.id > max_id).limit(100).all()
        if len(posts) == 0:
            return
        print("\n%d/%d" % (page, page_count))
        if not check_posts_for_danbooru_id(posts):
            return
        max_id = max(post.id for post in posts)
        page += 1


def check_posts_for_danbooru_id(posts):
    post_md5s = [post.md5 for post in posts]
    for i in range(0, len(post_md5s), 200):
        md5_sublist = post_md5s[i: i + 200]
        results = get_posts_by_md5s(md5_sublist)
        if results['error']:
            print(results['message'])
            return False
        if len(results['posts']) > 0:
            for post in posts:
                danbooru_post = next(filter(lambda x: x['md5'] == post.md5, results['posts']), None)
                if danbooru_post is None:
                    continue
                update_post_from_parameters(post, {'danbooru_id': danbooru_post['id']})
    return True


def check_posts_for_valid_md5():
    q = Post.query
    page = q.count_paginate(per_page=100)
    while True:
        print("\nPage #", page.page)
        for post in page.items:
            buffer = put_get_raw(post.file_path, 'rb')
            checksum = get_buffer_checksum(buffer)
            if post.md5 != checksum:
                print("\nMISMATCHING CHECKSUM: post #", post.id)
                for illust_url in post.illust_urls:
                    if redownload_post(post, illust_url, illust_url._source):
                        break
                else:
                    print("Unable to download!", 'post #', post.id)
            print(".", end="", flush=True)
        if not page.has_next:
            break
        page = page.next()
