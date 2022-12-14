"""Scrape metadata from target URL."""
import pprint

import requests
from bs4 import BeautifulSoup

from .scrape import (get_description,  # get_favicon,; get_theme_color
                     get_image, get_site_name, get_title)


def scrape_page_metadata(url):
    """Scrape target URL for metadata."""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }
    # pp = pprint.PrettyPrinter(indent=4)
    r = requests.get(url, headers=headers)
    html = BeautifulSoup(r.content, 'html.parser')
    metadata = {
        'title': get_title(html),
        'description': get_description(html),
        'image_url': get_image(html),
        'sitename': get_site_name(html, url),
        'url': url
        # 'favicon': get_favicon(html, url),
        # 'color': get_theme_color(html),
    }
    # pp.pprint(metadata)
    return metadata
