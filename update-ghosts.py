#!/usr/bin/env python

import multiprocessing
import re
import sys

import requests


base_url = 'http://www.expresso.net'
login_url = base_url + '/Account/Login'
ghosts_url = base_url + '/Rider/Ghost'


def find_links(link_name, text):
    pattern = r'href="([^"]+)">{}</a>'.format(link_name)
    links = re.findall(pattern, text)
    return [base_url + link for link in links]


def update_ghost(url):
    print url


if __name__ == '__main__':
    _, expresso_id, password = sys.argv

    # Attempt to login.
    payload = {
        'ExpressoId': expresso_id,
        'Password': password,
        }
    cookies = requests.post(login_url, payload).cookies
    if not '.ASPXAUTH' in cookies:
        print 'Error: login failed'
        sys.exit(1)

    # Search for links to change ghosts.
    ghosts_page = requests.get(ghosts_url, cookies=cookies).text
    urls = find_links('Change', ghosts_page)

    # Update ghosts asynchronously.
    pool = multiprocessing.Pool()
    pool.map_async(update_ghost, urls)
    pool.close()
    pool.join()
    
