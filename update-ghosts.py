#!/usr/bin/env python

import re
import sys

import requests


usage = '''Usage: {} [options] <ExpressoId> <Password>

    Options:
    -a --all-time   Take into account all results rather than only
                    those from the current season.
    -l --local      Only include results from your local facility.
    -v --verbose    Print the state of all ghosts, not just the ones
                    that have changed.'''

base_url = 'http://www.expresso.net'
login_url = base_url + '/Account/Login'
ghosts_url = base_url + '/Rider/Ghost'
leaderboard_url = base_url + '/Rider/Leaderboard/Details/{}' + \
                             '?leaderBoardLocation={}'


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
    first = re.findall(pattern, html)
    if first:
        url = base_url + first[0][0]
        name = first[0][1]
        return url, name
    else:
        return None

# Finds the link to challenge a ghost.
def find_challenge_url(html):
    pattern =r'action="([^"]+)"'
    url = re.findall(pattern, html)
    return base_url + url[0] if url else None


# Updates a ghost given it's change url.
def update_ghost(course_id):
    global cookies, all_time, local, verbose

    # Retrieve the leaderboard.
    url = leaderboard_url.format(
            course_id, 'Local' if local else 'Global&page=1')
    if all_time:
        url += '&seasonId=1'
    leaderboard = requests.get(url, cookies=cookies).text
    title = find_leaderboard_title(leaderboard)

    # Look at the first place person on the leaderboard.
    first_place =  find_first_place(leaderboard)
    label = '{} Leaderboard:'.format(title).ljust(32)
    if not first_place:
        if verbose:
            print 'No ghosts -- the leaderboard is empty!'
    else:
        ghost_url, name = first_place
        # Navigate to the ghost's page.
        ghost_info = requests.get(ghost_url, cookies=cookies).text
        # Actually change the ghost.
        challenge_url = find_challenge_url(ghost_info)
        if challenge_url is None:
            mesg = 'Ghost is up to date:'
        else:
            requests.post(challenge_url, headers = \
                    { 'content-length': '0' }, cookies=cookies).text
            mesg = 'Ghost changed to:'
        if verbose or 'changed' in mesg:
            print '{} {} {}'.format(label, mesg.ljust(20), name)


if __name__ == '__main__':
    usage = usage.format(sys.argv[0])

    # Process command arguments. (ugly as sin)
    if len(sys.argv) < 3:
        print usage
        sys.exit(2)
    expresso_id, password = sys.argv[-2:]
    all_time = False
    local = False
    verbose = False
    error = False
    for arg in sys.argv[1:-2]:
        if arg.startswith('--'):
            if arg == '--all-time':
                if all_time: error = True
                all_time = True
            elif arg == '--local':
                if local: error = True
                local = True
            elif arg == '--verbose':
                if verbose: error = True
                verbose = True
            else:
                error = True
        elif arg.startswith('-'):
            for flag in arg[1:]:
                if flag == 'a':
                    if all_time: error = True
                    all_time = True
                elif flag == 'l':
                    if local: error = True
                    local = True
                elif flag == 'v':
                    if verbose: error = True
                    verbose = True
                else:
                    error = True
        else:
            error = True
    if error:
        print usage
        sys.exit(2)

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
    for url in find_links('Change', ghosts_page):
        course_id = url.split('/')[-1]
        update_ghost(course_id)
