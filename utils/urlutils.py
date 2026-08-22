import re


def formaturl(url: str):
    if not re.match('(?:http|ftp|https)://', url):
        url = 'http://{}'.format(url)
        return url
    return url


def extractVideoId(url):
    regex = r"^https?\:\/\/(?:www\.youtube(?:\-nocookie)?\.com\/|m\.youtube\.com\/|youtube\.com\/)?(?:ytscreeningroom\?vi?=|youtu\.be\/|vi?\/|user\/.+\/u\/\w{1,2}\/|embed\/|watch\?(?:.*\&)?vi?=|\&vi?=|\?(?:.*\&)?vi?=)([^#\&\?\n\/<>\"']*)"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    else:
        return None


def checkUrlType(url):
    regex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
    match = re.search(regex, url)
    if match:
        if match.group(5) == 'results' or match.group(5) == 'channel' or match.group(5) == 'playlist':
            return 'bm'
        else:
            return 'yt'
    else:
        return 'bm'


def extractPlaylistId(url):
    regex = r"[\?&](list=)([a-zA-Z0-9\-_]+)"
    match = re.search(regex, url)
    if match:
        return match.group(2)
    else:
        return None


def getStartTime(url):  # todo do something
    regex = r"[\?|&](t=)(.\d*)"
    match = re.search(regex, url)
    if match:
        return match.group(2)
    else:
        return None


def getUrl(url):  # todo do something
    regex = r"[\?|&](t=)(.\d*)"
    test_str = url
    subst = ""
    result = re.sub(regex, subst, test_str, 0, re.MULTILINE)
    if result:
        return result


# --- YouTube ID validators (audit spec §4.1) -------------------------------
#
# VIDEO_ID_RE / PLAYLIST_ID_RE wrap the character domains the extractors
# above already accept (extractVideoId group 1, extractPlaylistId group 2),
# length-capped and anchored. CHANNEL_ID_RE / COMMENT_ID_RE / PAGE_TOKEN_RE
# are gap-fills for ID types with no existing coverage, using the same
# charset convention. All proxy views must pass user-supplied IDs through
# these before they reach googleapiclient -- non-conforming input is a
# client error (400), never an upstream API call.

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{11}$")
PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{12,64}$")
CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_\-]{22}$")
COMMENT_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{10,100}$")
PAGE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_=\-]{1,512}$")


def matches_id(value, regex):
    """True when ``value`` is a str conforming to the given ID regex."""
    return isinstance(value, str) and bool(regex.match(value))
