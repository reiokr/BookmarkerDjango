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
