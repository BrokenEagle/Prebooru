# APP/LOGICAL/UNSHORTEN_LINK.PY

# ## PYTHON IMPORTS
import re
import requests
import urllib.parse
from functools import reduce

# ##LOCAL IMPORTS
from .. import SESSION
from ..models import Domain, Description, ArtistUrl


# ##GLOBAL VARIABLES

SHORTLINK_DOMAINS = ['t.co', 'bit.ly']
NONSHORTLINK_DOMAINS = ['pixiv.me']

"""http://u0u1.net/Y8lp"""
SHORTURL_RG = re.compile(r'http://\w{3,5}\.\w{2,4}/\w{3,6}')

"""http://urx.morimo.info/Y8lp?h=u0u1.net"""
MORIMO_RG = re.compile(r'^http://urx\.morimo\.info/\w{3,6}\?h=\w{3,5}\.\w{2,4}$')

"""https://t.co/Rg6LqLPc4a"""
TCO_RG = re.compile(r'https?://t\.co/\w+')

SHORTLINK_DOMAIN_RG = None


# ##FUNCTIONS

def initialize_shortlinks():
    global SHORTLINK_DOMAINS, NONSHORTLINK_DOMAINS, SHORTLINK_DOMAIN_RG
    all_domains = Domain.query.all()
    SHORTLINK_DOMAINS += [domain.name for domain in all_domains if domain.redirector]
    NONSHORTLINK_DOMAINS += [domain.name for domain in all_domains if not domain.redirector]
    domain_re = '|'.join([re.escape(domain) for domain in SHORTLINK_DOMAINS])
    SHORTLINK_DOMAIN_RG = re.compile(r'https?://(?:%s)/' % (domain_re))


def get_known_domains():
    return set(SHORTLINK_DOMAINS + NONSHORTLINK_DOMAINS)


def check_initialization(func):
    def decorate(*args, **kwargs):
        if SHORTLINK_DOMAIN_RG is None:
            initialize_shortlinks()
        return func(*args, **kwargs)
    return decorate


def unshorten_links():  # Unused
    unshorten_descriptions()
    unshorten_artist_urls()


@check_initialization
def unshorten_artist_urls():
    artist_urls = ArtistUrl.query.filter(ArtistUrl.url.regexp_match('^' + SHORTLINK_DOMAIN_RG.pattern + '$')).all()
    return artist_urls
    for artist_url in artist_urls:
        artist_url.url = unshorten_text(artist_url.url)
    if len(artist_urls):
        SESSION.commit()


@check_initialization
def unshorten_descriptions():
    descriptions = Description.query.filter(Description.body.regexp_match(SHORTLINK_DOMAIN_RG.pattern)).all()
    return descriptions
    for descr in descriptions:
        descr.body = unshorten_tco_text(descr.body)
    if len(descriptions):
        SESSION.commit()


def unshorten_text(text):
    transforms = get_transforms(text)
    for key in transforms:
        text = text.replace(key, transforms[key])
    return text


@check_initialization
def get_transforms(text):
    short_links = SHORTLINK_DOMAIN_RG.findall(text)
    transforms = {}
    for link in short_links:
        redirect_link = get_redirect(link)
        if redirect_link is not None:
            transforms[link] = redirect_link
    return transforms


def get_redirect(link, level=0):
    if level > 3:
        return link
    try:
        resp = requests.head(link, allow_redirects=None, timeout=5)
    except Exception as e:
        print("Error getting URL redirect:", link, e)
        return
    if resp.status_code in [301, 302] and 'location' in resp.headers:
        redirect_link = resp.headers['location']
        if is_morimo_link(redirect_link) or is_short_link(redirect_link) or is_schema_change_only(link, redirect_link):
            redirect_link = get_redirect(redirect_link, level + 1)
        return redirect_link
    return link


@check_initialization
def find_short_domains():  # Unused

    def _find_short_domain(acc, text):
        return acc + re.findall(r'http://\w{3,5}\.\w{2,4}/\w{3,6}', text)

    artist_urls = ArtistUrl.query.filter(ArtistUrl.url.regexp_match('^' + SHORTURL_RG.pattern + '$')).all()
    urls = [url.url for url in artist_urls]
    shortlinks = set(reduce(_find_short_domain, urls, []))
    descriptions = Description.query.filter(Description.body.regexp_match(SHORTURL_RG.pattern)).all()
    descrs = [descr.body for descr in descriptions]
    shortlinks = shortlinks.union(reduce(_find_short_domain, descrs, []))
    added_domains = []
    known_domains = get_known_domains()
    while True:
        unknown_shortlinks = [link for link in shortlinks if urllib.parse.urlparse(link).netloc not in known_domains]
        if len(unknown_shortlinks) == 0:
            break
        link = unknown_shortlinks[0]
        parse = urllib.parse.urlparse(link)
        redirect_link = get_redirect(link)
        if link == redirect_link or is_schema_change_only(link, redirect_link):
            added_domains.append(Domain(name=parse.netloc, redirector=False))
            NONSHORTLINK_DOMAINS.append(parse.netloc)
        else:
            added_domains.append(Domain(name=parse.netloc, redirector=True))
            SHORTLINK_DOMAINS.append(parse.netloc)
        known_domains.add(parse.netloc)
    if len(added_domains):
        SESSION.add_all(added_domains)
        SESSION.commit()


def unshorten_all_links():  # Unused
    unshorten_tco_links()


# General

def get_short_transformations(text):  # Unused
    shortlinks = SHORTURL_RG.findall(text)
    transforms = {}
    for link in shortlinks:
        redirect_link = get_redirect(link)
        if redirect_link is not None:
            transforms[link] = redirect_link
    return transforms


# Morimo

def is_morimo_link(link):
    return MORIMO_RG.match(link) is not None


def is_short_link(link):
    return SHORTURL_RG.match(link) is not None


def is_schema_change_only(original_link, redirect_link):
    original_parse = urllib.parse.urlparse(original_link)
    redirect_parse = urllib.parse.urlparse(redirect_link)
    return (original_parse.scheme != redirect_parse.scheme) and (original_parse.netloc == redirect_parse.netloc) and\
           (original_parse.path == redirect_parse.path)


# T.CO -- Twitter

def unshorten_tco_links():
    unshorten_tco_descriptions()
    unshorten_tco_artist_urls()


def unshorten_tco_artist_urls():
    tco_artist_urls = ArtistUrl.query.filter(ArtistUrl.url.like('https://t.co/%')).all()
    for artist_url in tco_artist_urls:
        artist_url.url = unshorten_tco_text(artist_url.url)
    if len(tco_artist_urls):
        SESSION.commit()


def unshorten_tco_descriptions():
    tco_descriptions = Description.query.filter(Description.body.like('%https://t.co/%')).all()
    for descr in tco_descriptions:
        descr.body = unshorten_tco_text(descr.body)
    if len(tco_descriptions):
        SESSION.commit()


def unshorten_tco_text(text):
    transforms = get_tco_transforms(text)
    for key in transforms:
        text = text.replace(key, transforms[key])
    return text


def get_tco_transforms(text):
    tco_links = TCO_RG.findall(text)
    transforms = {}
    for link in tco_links:
        transforms[link] = None
        try:
            resp = requests.get(link, allow_redirects=None, timeout=5)
        except Exception:
            print("Error getting URL redirect:", link)
            continue
        if resp.status_code == 301 and 'location' in resp.headers:
            transforms[link] = resp.headers['location']
    return transforms
