# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
from flask import request, jsonify
import atexit
import threading
from PIL import Image
import imagehash
import distance
import requests
from io import BytesIO
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from argparse import ArgumentParser
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app import PREBOORU_APP, SESSION
import app.models
from app.models import Post
from app.cache import MediaFile
from app.similarity.similarity_data import SimilarityData, HASH_SIZE
from app.similarity.similarity_pool import SimilarityPool
from app.similarity.similarity_pool_element import SimilarityPoolElement
from app.logical.file import PutGetRaw, CreateDirectory
from app.logical.utility import GetCurrentTime, GetBufferChecksum, DaysFromNow, SetError, SecondsFromNowLocal
from app.logical.network import GetHTTPFile
from app.logical.file import LoadDefault, PutGetJSON
from app.sources.base_source import GetImageSource, NoSource
from app.database.similarity_pool_element_db import BatchDeleteSimilarityPoolElement
from app.storage import CACHE_DATA_DIRECTORY
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, SIMILARITY_PORT, DEBUG_MODE, VERSION


# ## GLOBAL VARIABLES

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'similarity-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

SCHED = None
SIMILARITY_SEM = threading.Semaphore()
GENERATE_SEM = threading.Semaphore()

TOTAL_BITS = HASH_SIZE * HASH_SIZE


# ## FUNCTIONS

# #### Route functions

@PREBOORU_APP.route('/check_similarity.json', methods=['GET'])
def check_similarity():
    request_urls = request.args.getlist('urls[]')
    request_score = request.args.get('score', type=float, default=90.0)
    use_original = request.args.get('use_original', type=bool, default=False)
    include_posts = request.args.get('include_posts', type=bool, default=False)
    retdata = {'error': False}
    if request_urls is None:
        return SetError(retdata, "Must include url.")
    similar_results = []
    for image_url in request_urls:
        source = GetImageSource(image_url) or NoSource()
        download_url = source.SmallImageUrl(image_url) if source is not None and not use_original else image_url
        media = MediaFile.query.filter_by(media_url=download_url).first()
        if media is None:
            media, image = CreateNewMedia(download_url, source)
            if type(image) is str:
                return SetError(retdata, image)
        else:
            image = Image.open(media.file_path)
        image = image.copy().convert("RGB")
        image_hash = str(imagehash.whash(image, hash_size=HASH_SIZE))
        ratio = round(image.width / image.height, 4)
        smatches = SimilarityData.query.filter(SimilarityData.ratio_clause(ratio), SimilarityData.cross_similarity_clause2(image_hash)).all()
        score_results = CheckSimilarMatchScores(smatches, image_hash, request_score)
        all_post_ids = set(result['post_id'] for result in score_results)
        final_results = []
        for post_id in all_post_ids:
            post_results = [result for result in score_results if result['post_id'] == post_id]
            if len(post_results) > 1:
                post_results = sorted(post_results, key=lambda x: x['score'], reverse=True)
            final_results.append(post_results[0])
        final_results = sorted(final_results, key=lambda x: x['score'], reverse=True)
        if include_posts:
            post_ids = [result['post_id'] for result in final_results]
            posts = app.models.Post.query.filter(app.models.Post.id.in_(post_ids)).all()
            for result in final_results:
                post = next(filter(lambda x: x.id == result['post_id'], posts), None)
                result['post'] = post.to_json() if post is not None else post
        normalized_url = source.NormalizedImageUrl(image_url) if not use_original else image_url
        similar_results.append({'image_url': normalized_url, 'post_results': final_results, 'cache': media.file_url})
    retdata['similar_results'] = similar_results
    return retdata


@PREBOORU_APP.route('/generate_similarity.json', methods=['POST'])
def generate_similarity():
    data = request.get_json()
    if 'post_ids' not in data or len(data['post_ids']) == 0:
        return {'error': True, 'message': "Must include post_ids."}
    GENERATE_SEM.acquire()
    print("\n<generate semaphore acquire>\n")
    try:
        posts = Post.query.filter(Post.id.in_(data['post_ids'])).all()
        for post in posts:
            print("Regenerating post #", post.id)
            SimilarityData.query.filter_by(post_id=post.id).delete()
            SESSION.commit()
            GeneratePostSimilarity(post)
            pool = SimilarityPool.query.filter_by(post_id=post.id).first()
            if pool is not None and len(pool.elements) > 0:
                print("Deleting similarity pool elements:", len(pool.elements))
                BatchDeleteSimilarityPoolElement(pool.elements)
            sdata_items = SimilarityData.query.filter_by(post_id=post.id).all()
            PopulateSimilarityPools(sdata_items)
    finally:
        GENERATE_SEM.release()
        print("\n<generate semaphore release>\n")
    return {'error': False}


@PREBOORU_APP.route('/check_posts', methods=['GET'])
def check_posts():
    SCHED.add_job(ProcessSimilarity)
    return jsonify(SIMILARITY_SEM._value > 0)


# #### Helper functions

def HexToBinary(inhex):
    return bin(int(inhex, 16))[2:].zfill(len(inhex * 4))


def LoadImage(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return "Error processing image data: %s" % repr(e)
    return image


# #### Auxiliary functions

def ChooseSimilarityResult():
    while True:
        keyinput = input("Post ID: ")
        if not keyinput:
            return
        if not keyinput.isdigit():
            print("Must enter a valid ID number.")
            continue
        post_id = int(keyinput)
        sresult = SimilarityData.query.filter_by(post_id=post_id).first()
        if sresult is None:
            print("Post not found:", post_id)
            continue
        return sresult


def CheckSimilarMatchScores(similarity_results, image_hash, min_score):
    found_results = []
    image_binary_string = HexToBinary(image_hash)
    hamming_time = 0
    for sresult in similarity_results:
        sresult_binary_string = HexToBinary(sresult.image_hash)
        starttime = time.time()
        mismatching_bits = distance.hamming(image_binary_string, sresult_binary_string)
        endtime = time.time()
        hamming_time += (endtime - starttime)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        if score >= min_score:
            data = {
                'post_id': sresult.post_id,
                'score': score,
            }
            found_results.append(data)
    return sorted(found_results, key=lambda x: x['score'], reverse=True)


def GetSimilarMatches(image_hash, ratio):
    ratio_low = round(ratio * 99, 4) / 100
    ratio_high = round(ratio * 101, 4) / 100
    q = SimilarityData.query
    q = q.filter(SimilarityData.ratio.between(ratio_low, ratio_high))
    q = q.filter(SimilarityData.cross_similarity_clause2(image_hash))
    return q.all()


def CreateNewMedia(download_url, source):
    buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        return None, "Exception processing download: %s" % repr(buffer)
    if isinstance(buffer, requests.Response):
        return None, "HTTP %d - %s" % (buffer.status_code, buffer.reason)
    image = LoadImage(buffer)
    if type(image) is str:
        return None, image
    md5 = GetBufferChecksum(buffer)
    extension = source.GetMediaExtension(download_url)
    media = MediaFile(md5=md5, file_ext=extension, media_url=download_url, expires=DaysFromNow(1))
    CreateDirectory(CACHE_DATA_DIRECTORY)
    PutGetRaw(media.file_path, 'wb', buffer)
    SESSION.add(media)
    SESSION.commit()
    return media, image


def ProcessSimilarity():
    SIMILARITY_SEM.acquire()
    print("\n<similarity semaphore acquire>\n")
    try:
        while True:
            if not ProcessSimilaritySet():
                break
        while True:
            if not ProcessSimilarityPool():
                break
    finally:
        SIMILARITY_SEM.release()
        print("\n<similarity semaphore release>\n")


# #### Similarity data functions

def RegeneratePostSimilarity(result, post):
    image = Image.open(post.preview_path)
    image_hash = imagehash.whash(image, hash_size=HASH_SIZE)
    result.image_hash = str(image_hash)
    SESSION.commit()


def GeneratePostSimilarity(post):
    ratio = round(post.width / post.height, 4)
    preview_image = Image.open(post.preview_path)
    preview_image = preview_image.convert("RGB")
    preview_image_hash = str(imagehash.whash(preview_image, hash_size=HASH_SIZE))
    print("PREVIEW SIZE ADD")
    simresult = SimilarityData(post_id=post.id, image_hash=preview_image_hash, ratio=ratio)
    SESSION.add(simresult)
    SESSION.commit()
    simresults = [simresult]
    if post.file_ext != 'mp4':
        full_image = Image.open(post.file_path)
        full_image = full_image.convert("RGB")
        full_image_hash = str(imagehash.whash(full_image, hash_size=HASH_SIZE))
        score_results = CheckSimilarMatchScores(simresults, full_image_hash, 90.0)
        if len(score_results) == 0:
            print("FULL SIZE ADD")
            simresult = SimilarityData(post_id=post.id, image_hash=full_image_hash, ratio=ratio)
            SESSION.add(simresult)
            SESSION.commit()
            simresults.append(simresult)
    if post.file_path != post.sample_path:
        sample_image = Image.open(post.sample_path)
        sample_image = sample_image.convert("RGB")
        sample_image_hash = str(imagehash.whash(sample_image, hash_size=HASH_SIZE))
        score_results = CheckSimilarMatchScores(simresults, sample_image_hash, 90.0)
        if len(score_results) == 0:
            print("SAMPLE SIZE ADD")
            simresult = SimilarityData(post_id=post.id, image_hash=sample_image_hash, ratio=ratio)
            SESSION.add(simresult)
            SESSION.commit()


def ProcessSimilaritySet():
    max_post_id = SESSION.query(func.max(SimilarityData.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).paginate(per_page=100)
    if len(page.items) == 0:
        print("ProcessSimilaritySet: no posts to process")
        return False
    print("Generating post similarity data.")
    while True:
        for post in page.items:
            GeneratePostSimilarity(post)
        if not page.has_next:
            return True
        page = page.next()


# #### Similarity pool functions

def PopulateSimilarityPools(sdata_items):
    print("Generating post similarity pool.")
    total_matches = []
    score_results = []
    for sdata in sdata_items:
        smatches = SimilarityData.query.filter(SimilarityData.ratio_clause(sdata.ratio), SimilarityData.cross_similarity_clause2(sdata.image_hash), SimilarityData.post_id != sdata.post_id).all()
        score_results += CheckSimilarMatchScores(smatches, sdata.image_hash, 90.0)
        total_matches += smatches
    sibling_post_ids = set(result['post_id'] for result in score_results)
    sibling_pools = SimilarityPool.query.options(selectinload(SimilarityPool.elements)).filter(SimilarityPool.post_id.in_(sibling_post_ids)).all()
    final_results = []
    for post_id in sibling_post_ids:
        post_results = [result for result in score_results if result['post_id'] == post_id]
        post_result = sorted(post_results, key=lambda x: x['score'], reverse=True)[0]
        final_results.append(post_result)
    main_pool, index = CreateSimilarityPools(sdata.post_id, final_results, sibling_pools)
    if index is not None:
        CreateSimilarityPairings(sdata.post_id, final_results, main_pool, sibling_pools, index)


def CreateSimilarityPools(post_id, score_results, sibling_pools):
    current_time = GetCurrentTime()
    main_pool = SimilarityPool.query.filter_by(post_id=post_id).first()
    if main_pool is None:
        main_pool = SimilarityPool(post_id=post_id, created=current_time, element_count=0)
        SESSION.add(main_pool)
    main_pool.updated = current_time
    SESSION.commit()
    if len(score_results) == 0:
        return main_pool, None
    sibling_post_ids = [spool.post_id for spool in sibling_pools]
    INDEX_POOL_BY_POST_ID = {pool.post_id: pool for pool in sibling_pools}
    add_pools = []
    for post_id in sibling_post_ids:
        if post_id not in INDEX_POOL_BY_POST_ID:
            pool = SimilarityPool(post_id=post_id, created=current_time, updated=current_time)
            add_pools.append(pool)
            INDEX_POOL_BY_POST_ID[post_id] = pool
    if len(add_pools) > 0:
        SESSION.add_all(add_pools)
        SESSION.commit()
    return main_pool, INDEX_POOL_BY_POST_ID


def CreateSimilarityPairings(post_id, score_results, main_pool, sibling_pools, index):
    INDEX_POOL_BY_POST_ID = index
    # Need to check for existing score results
    main_post_ids = [element.post_id for element in main_pool.elements]
    INDEX_POST_IDS_BY_POST_ID = {pool.post_id: [element.post_id for element in pool.elements] for pool in sibling_pools}
    for result in score_results:
        print("Creating score result sibling pairs:", result)
        if result['post_id'] in main_post_ids:
            spe1 = next(filter(lambda x: x.post_id == result['post_id'], main_pool.elements))
        else:
            spe1 = SimilarityPoolElement(pool_id=main_pool.id, **result)
            SESSION.add(spe1)
            SESSION.commit()
            main_pool.element_count = main_pool._get_element_count()
            SESSION.commit()
        sibling_pool_post_ids = INDEX_POST_IDS_BY_POST_ID[result['post_id']] if result['post_id'] in INDEX_POST_IDS_BY_POST_ID else []
        if post_id in sibling_pool_post_ids:
            sibling_pool = INDEX_POOL_BY_POST_ID[result['post_id']]
            spe2 = next(filter(lambda x: x.post_id == post_id, sibling_pool.elements))
        else:
            sibling_pool = INDEX_POOL_BY_POST_ID[result['post_id']]
            spe2 = SimilarityPoolElement(pool_id=sibling_pool.id, post_id=post_id, score=result['score'])
            SESSION.add(spe2)
            SESSION.commit()
            sibling_pool.element_count = sibling_pool._get_element_count()
            SESSION.commit()
        print("Sibling pair:", spe1.id, '<->', spe2.id)
        spe1.sibling_id = spe2.id
        spe2.sibling_id = spe1.id
        SESSION.commit()


def ProcessSimilarityPool():
    max_post_id = SESSION.query(func.max(SimilarityPool.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).with_entities(Post.id).paginate(per_page=100)
    while True:
        all_post_ids = [x[0] for x in page.items]
        all_sdata_items = SimilarityData.query.filter(SimilarityData.post_id.in_(all_post_ids)).all()
        for post_id in all_post_ids:
            sdata_items = [sdata for sdata in all_sdata_items if sdata.post_id == post_id]
            PopulateSimilarityPools(sdata_items)
        if not page.has_next:
            break
        page = page.next()


# #### Main execution functions

def GenerateSimilarityResults(args):
    if args.expunge:
        SimilarityData.query.delete()
        SESSION.commit()
    max_post_id = SESSION.query(func.max(SimilarityData.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).paginate(per_page=100)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            GeneratePostSimilarity(post)
        if not page.has_next:
            break
        page = page.next()
    print("Done!")


def GenerateSimilarityPools(args):
    if args.expunge:
        SimilarityPoolElement.query.delete()  # This may not work due to the sibling relationship; may need to do a mass update first
        SESSION.commit()
        SimilarityPool.query.delete()
        SESSION.commit()
    max_post_id = SESSION.query(func.max(SimilarityPool.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).with_entities(Post.id).paginate(per_page=100)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        all_post_ids = [x[0] for x in page.items]
        all_sdata_items = SimilarityData.query.filter(SimilarityData.post_id.in_(all_post_ids)).all()
        for post_id in all_post_ids:
            sdata_items = [sdata for sdata in all_sdata_items if sdata.post_id == post_id]
            PopulateSimilarityPools(sdata_items)
        if not page.has_next:
            break
        page = page.next()
    print("Done!")


def ComparePostSimilarity(args):
    sresult = ChooseSimilarityResult()
    if sresult is None:
        return
    print("Result hash:", sresult.image_hash)
    sresult_binary_string = HexToBinary(sresult.image_hash)
    while True:
        keyinput = input("Image URL: ")
        if not keyinput:
            break
        buffer = GetHTTPFile(keyinput)
        if type(buffer) is not bytes:
            continue
        try:
            file_imgdata = BytesIO(buffer)
            image = Image.open(file_imgdata)
        except Exception as e:
            print("Unable to open image:", e)
            continue
        image.copy().convert("RGB")
        image_hash = str(imagehash.whash(image, hash_size=HASH_SIZE))
        print("Image hash:", image_hash)
        image_binary_string = HexToBinary(image_hash)
        mismatching_bits = distance.hamming(image_binary_string, sresult_binary_string)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        print("Mismatching:", mismatching_bits, "Ratio:", miss_ratio, "Score:", score)


def ComparePosts(args):
    page = Post.query.order_by(Post.id.asc()).paginate(per_page=100)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            print("Post #", post.id)
            starttime = time.time()
            ratio = round(post.width / post.height, 4)
            simresults = SimilarityData.query.filter_by(post_id=post.id).all()
            if post.file_ext != 'mp4':
                full_image = Image.open(post.file_path)
                full_image = full_image.convert("RGB")
                full_image_hash = str(imagehash.whash(full_image, hash_size=HASH_SIZE))
                print("Full convert time:", time.time() - starttime)
                score_results = CheckSimilarMatchScores(simresults, full_image_hash, 90.0)
                if len(score_results) == 0:
                    print("FULL SIZE ADD")
                    simresult = SimilarityData(post_id=post.id, image_hash=full_image_hash, ratio=ratio)
                    SESSION.add(simresult)
                    SESSION.commit()
                    simresults.append(simresult)
                if post.file_path == post.sample_path:
                    continue
            starttime = time.time()
            sample_image = Image.open(post.sample_path)
            sample_image = sample_image.convert("RGB")
            sample_image_hash = str(imagehash.whash(sample_image, hash_size=HASH_SIZE))
            print("Sample convert time:", time.time() - starttime)
            score_results = CheckSimilarMatchScores(simresults, sample_image_hash, 90.0)
            if len(score_results) == 0:
                print("SAMPLE SIZE ADD")
                simresult = SimilarityData(post_id=post.id, image_hash=sample_image_hash, ratio=ratio)
                SESSION.add(simresult)
                SESSION.commit()
        if not page.has_next:
            break
        page = page.next()
    print("Done!")


def StartServer(args):
    if args.title:
        os.system('title Similarity Server')
    global SCHED, SERVER_PID
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n========== Starting server - Similarity-%s ==========" % VERSION)
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
        SCHED = BackgroundScheduler(daemon=True)
        SCHED.add_job(ProcessSimilarity, next_run_time=SecondsFromNowLocal(5))
        SCHED.start()
    PREBOORU_APP.name = 'similarity'
    PREBOORU_APP.run(threaded=True, port=SIMILARITY_PORT)


# #### Initialization

os.environ['FLASK_ENV'] = 'development' if DEBUG_MODE else 'production'

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])
    if SCHED is not None and SCHED.running:
        SCHED.shutdown()


# #### Main function

def Main(args):
    switcher = {
        'generate': GenerateSimilarityResults,
        'pools': GenerateSimilarityPools,
        'compare': ComparePostSimilarity,
        'compareposts': ComparePosts,
        'server': StartServer,
    }
    switcher[args.type](args)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('type', choices=['generate', 'pools', 'compare', 'compareposts', 'server'])
    parser.add_argument('--expunge', required=False, default=False, action="store_true", help="Expunge all similarity records.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    parser.add_argument('--lastid', required=False, type=int, help="Sets the last post ID to use.")
    args = parser.parse_args()
    Main(args)
