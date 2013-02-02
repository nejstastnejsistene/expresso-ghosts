#!/usr/bin/env python

import multiprocessing
import re
import sys

import requests


base_url = 'http://www.expresso.net'
login_url = base_url + '/Account/Login'
ghosts_url = base_url + '/Rider/Ghost'


# Searches for links with the given name.
def find_links(link_name, html):
    pattern = r'href="([^"]+)">{}</a>'.format(link_name)
    links = re.findall(pattern, html)
    return [base_url + link for link in links]

# Finds the name of the course from its leaderboard.
def find_leaderboard_title(html):
    pattern = r'<h2>([^<]+)</h2>'
    return re.findall(pattern, html)[0].strip()

# Finds the first place person on a leaderboard
def find_first_place(html):
    pattern = r'1\s*</td>\s*<td[^>]*>\s*<a href="([^"]+)">([^>]*)</a>'
    return re.findall(pattern, html)[0]

# Finds the link to challenge a ghost.
def find_challenge_url(html):
    pattern =r'action="([^"]+)"'
    return re.findall(pattern, html)[0]


# Updates a ghost given it's change url.
def update_ghost(url):
    global cookies, all_time, local

    # Retrieve the leaderboard.
    html = requests.get(url, cookies=cookies).text
    url = find_links('My Facility' if local else 'Global', html)[0]
    if all_time:
        url += '&seasonId=1'
    leaderboard = requests.get(url, cookies=cookies).text
    title = find_leaderboard_title(leaderboard)

    # Look at the first place person on the leaderboard.
    first_place =  find_first_place(leaderboard)
    print '{} Leaderboard:'.format(title).ljust(30),
    if not first_place:
        print 'No ghosts -- the leaderboard is empty!'
    else:
        ghost_url, name = first_place
        if '(Ghost)' in name:
            mesg = 'Ghost is up to date:'
        else:
            # Navigate to the ghost's page.
            ghost_url = base_url + ghost_url
            ghost_info = requests.get(ghost_url, cookies=cookies).text
            # Actually change the ghost.
            challenge_url = base_url + find_challenge_url(ghost_info)
            requests.post(challenge_url, headers= \
                    { 'content-length': '0' }, cookies=cookies).text
            mesg = 'Ghost changed to:'
        print '{} {}'.format(mesg.ljust(20), name)


if __name__ == '__main__':
    local = True
    all_time = True
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
    
