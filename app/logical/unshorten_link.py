# APP/LOGICAL/UNSHORTEN_LINK.PY

# ##PYTHON IMPORTS
import re
import requests
import urllib.parse
from functools import reduce

# ##LOCAL IMPORTS
from .. import SESSION
from ..cache import Domain
from ..models import Description, ArtistUrl


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

def InitializeShortlinks():
    global SHORTLINK_DOMAINS, NONSHORTLINK_DOMAINS, SHORTLINK_DOMAIN_RG
    all_domains = Domain.query.all()
    SHORTLINK_DOMAINS += [domain.name for domain in all_domains if domain.redirector]
    NONSHORTLINK_DOMAINS += [domain.name for domain in all_domains if not domain.redirector]
    SHORTLINK_DOMAIN_RG = re.compile(r'https?://(?:%s)/' % ('|'.join([re.escape(domain) for domain in SHORTLINK_DOMAINS])))


def GetKnownDomains():
    return set(SHORTLINK_DOMAINS + NONSHORTLINK_DOMAINS)


def CheckInitialization(func):
    def decorate(*args, **kwargs):
        if SHORTLINK_DOMAIN_RG is None:
            InitializeShortlinks()
        return func(*args, **kwargs)
    return decorate


def UnshortenLinks():
    UnshortenDescriptions()
    UnshortenArtistUrls()


@CheckInitialization
def UnshortenArtistUrls():
    print("UnshortenArtistUrls")
    artist_urls = ArtistUrl.query.filter(ArtistUrl.url.regexp_match('^' + SHORTLINK_DOMAIN_RG.pattern + '$')).all()
    return artist_urls
    for artist_url in artist_urls:
        artist_url.url = UnshortenText(artist_url.url)
    if len(artist_urls):
        SESSION.commit()


@CheckInitialization
def UnshortenDescriptions():
    print("UnshortenArtistUrls")
    descriptions = Description.query.filter(Description.body.regexp_match(SHORTLINK_DOMAIN_RG.pattern)).all()
    return descriptions
    for descr in descriptions:
        descr.body = UnshortenTcoText(descr.body)
    if len(descriptions):
        SESSION.commit()


def UnshortenText(text):
    transforms = GetTransforms(text)
    for key in transforms:
        text = text.replace(key, transforms[key])
    return text


@CheckInitialization
def GetTransforms(text):
    short_links = SHORTLINK_DOMAIN_RG.findall(text)
    transforms = {}
    print("GetTransforms:", len(short_links))
    for link in short_links:
        redirect_link = GetRedirect(link)
        if redirect_link is not None:
            transforms[link] = redirect_link
    return transforms


def GetRedirect(link, level=0):
    if level > 3:
        return link
    try:
        resp = requests.head(link, allow_redirects=None, timeout=5)
    except Exception as e:
        print("Error getting URL redirect:", link, e)
        return
    if resp.status_code in [301, 302] and 'location' in resp.headers:
        redirect_link = resp.headers['location']
        if IsMorimoLink(redirect_link) or IsShortLink(redirect_link) or IsSchemaChangeOnly(link, redirect_link):
            redirect_link = GetRedirect(redirect_link, level + 1)
        return redirect_link
    return link


@CheckInitialization
def FindShortDomains():
    artist_urls = ArtistUrl.query.filter(ArtistUrl.url.regexp_match('^' + SHORTURL_RG.pattern + '$')).all()
    shortlinks = set(reduce(lambda acc, x: acc + re.findall(r'http://\w{3,5}\.\w{2,4}/\w{3,6}', x.url), artist_urls, []))
    descriptions = Description.query.filter(Description.body.regexp_match(SHORTURL_RG.pattern)).all()
    shortlinks = shortlinks.union(reduce(lambda acc, x: acc + re.findall(r'http://\w{3,5}\.\w{2,4}/\w{3,6}', x.body), descriptions, []))
    added_domains = []
    known_domains = GetKnownDomains()
    while True:
        unknown_shortlinks = [link for link in shortlinks if urllib.parse.urlparse(link).netloc not in known_domains]
        if len(unknown_shortlinks) == 0:
            break
        link = unknown_shortlinks[0]
        parse = urllib.parse.urlparse(link)
        print("FindShortDomains: checking - ", parse.netloc)
        redirect_link = GetRedirect(link)
        if link == redirect_link or IsSchemaChangeOnly(link, redirect_link):
            added_domains.append(Domain(name=parse.netloc, redirector=False))
            NONSHORTLINK_DOMAINS.append(parse.netloc)
        else:
            added_domains.append(Domain(name=parse.netloc, redirector=True))
            SHORTLINK_DOMAINS.append(parse.netloc)
        known_domains.add(parse.netloc)
    if len(added_domains):
        SESSION.add_all(added_domains)
        SESSION.commit()


def UnshortenAllLinks():
    UnshortenTcoLinks()


# General

def GetShortTransformations(text):
    shortlinks = SHORTURL_RG.findall(text)
    print("GetShortTransformations:", len(shortlinks))
    transforms = {}
    for link in shortlinks:
        redirect_link = GetRedirect(link)
        if redirect_link is not None:
            transforms[link] = redirect_link
    return transforms


# Morimo

def IsMorimoLink(link):
    return MORIMO_RG.match(link) is not None


def IsShortLink(link):
    return SHORTURL_RG.match(link) is not None


def IsSchemaChangeOnly(original_link, redirect_link):
    original_parse = urllib.parse.urlparse(original_link)
    redirect_parse = urllib.parse.urlparse(redirect_link)
    return (original_parse.scheme != redirect_parse.scheme) and (original_parse.netloc == redirect_parse.netloc) and (original_parse.path == redirect_parse.path)


# T.CO -- Twitter

def UnshortenTcoLinks():
    UnshortenTcoDescriptions()
    UnshortenTcoArtistUrls()


def UnshortenTcoArtistUrls():
    print("UnshortenTcoArtistUrls")
    tco_artist_urls = ArtistUrl.query.filter(ArtistUrl.url.like('https://t.co/%')).all()
    for artist_url in tco_artist_urls:
        artist_url.url = UnshortenTcoText(artist_url.url)
    if len(tco_artist_urls):
        SESSION.commit()


def UnshortenTcoDescriptions():
    print("UnshortenTcoDescriptions")
    tco_descriptions = Description.query.filter(Description.body.like('%https://t.co/%')).all()
    for descr in tco_descriptions:
        descr.body = UnshortenTcoText(descr.body)
    if len(tco_descriptions):
        SESSION.commit()


def UnshortenTcoText(text):
    transforms = GetTcoTransforms(text)
    for key in transforms:
        text = text.replace(key, transforms[key])
    return text


def GetTcoTransforms(text):
    tco_links = TCO_RG.findall(text)
    transforms = {}
    print("GetTcoTransforms:", len(tco_links))
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
