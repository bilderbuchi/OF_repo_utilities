"""
A set of small helper functions for interacting with Github repositories
(primarily openFrameworks) via PyGithub.

Requires Python3
"""

import os
import sys
import inspect
import webbrowser
from subprocess import check_call, CalledProcessError, DEVNULL
from github import Github
import psutil

if sys.version_info < (3, 0):
    sys.exit('github_tools requires Python 3.0 or greater')
# TODO: See if a py2/py3 compatible codebase can reasonably be achieved.
# TODO: Add a convenience function returning rate limit info
# TODO: Check proper PY3 UTF-8 string handling


def get_github_instance(token='github_token.txt', timeout=20):
    """Return a token-authenticated Github instance."""

    currentdir = os.path.dirname(os.path.abspath(
                                 inspect.getfile(inspect.currentframe()))
                                 )
    tokenpath = os.path.join(currentdir, token)

    try:
        with open(tokenpath) as token_file:
            my_token = token_file.readline().rstrip('\n')
    except FileNotFoundError:
        sys.exit('Token file ' + tokenpath + ' not found.\n' +
                 'Please create it, containing your Github access token.')

    return Github(my_token, timeout=timeout)


def get_repo(user='openframeworks', repo='openFrameworks',
             token='github_token.txt', timeout=20):
    """Return Github authenticated repo, ready for use."""

    G = get_github_instance(token=token, timeout=timeout)
    return G.get_user(user).get_repo(repo)


def open_in_browser(list_of_urls):
    """Offer to open a list of URLs in the browser."""

    if list_of_urls:
        answer = input('Press "y" to open all issues in the browser, ' +
                       'other key to quit:\n')
        if answer.lower() == 'y':
            print('Opening...')
            for u in list_of_urls:
                webbrowser.open(u)
            print('Done')


def validate_tagname(repo, tagname):
    """Try to find a given tagname in a repo's tags.

    If no tagname is given, find the youngest tag.
    Return a dict containing tag name and tag date
    """

    print('Fetching tags...')
    tags = repo.get_tags()
    tag_list = []
    for t in tags:
        tag_list.append({'name': t.name,
                         'date': t.commit.commit.committer.date})

    if not tagname:
        # no tagname was given, choose the youngest tag
        tag = max(tag_list, key=lambda x: x['date'])
    else:
        # find date for given tagname
        for t in tag_list:
            if tagname == t['name']:
                tag = t
                break
        else:
            # no appropriate tag was found
            sys.exit('Tag name ' + tagname + ' not found, aborting!')
    print('Selected tag ' + tag['name'] + ', date: ' + str(tag['date']))
    return tag


def local_repo_location(location_file='local_repo_location.txt'):
    """Return the path to a local Git repo, if defined in a location file."""

    currentdir = os.path.dirname(os.path.abspath(
                                 inspect.getfile(inspect.currentframe()))
                                 )
    location_file_path = os.path.join(currentdir, location_file)

    try:
        with open(location_file_path) as location_file:
            repo_location = os.path.abspath(location_file.readline().rstrip())
            # Confirm valid Git repo existence
            check_call(['git', 'rev-parse', '--is-inside-work-tree'],
                       stdout=DEVNULL,
                       cwd=repo_location)
            print('Found Git repo at ' + str(repo_location))
            return repo_location
    except FileNotFoundError:
        print('Location file ' + location_file_path + ' not found.')
        return None
    except CalledProcessError:
        sys.exit(str(repo_location) + ' is not a valid Git repository!')


def log_traffic():
    """Log consumed network bandwidth since last call to console."""

    my_io = psutil.net_io_counters
    try:
        log_traffic.store['kB_recv'].append(my_io().bytes_recv/1000)
        log_traffic.store['kB_sent'].append(my_io().bytes_sent/1000)
        print('Traffic: ' +
              '{0:.2f}kB down / '.format(log_traffic.store['kB_recv'][-1] -
                                         log_traffic.store['kB_recv'][-2]) +
              '{0:.2f}kB up'.format(log_traffic.store['kB_sent'][-1] -
                                    log_traffic.store['kB_sent'][-2]))
    except AttributeError:  # store not initialized yet
        log_traffic.store = {'kB_recv': [my_io().bytes_recv/1000],
                             'kB_sent': [my_io().bytes_sent/1000]}
