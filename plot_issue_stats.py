#!/usr/bin/env python3
"""Main script for openFrameworks Github issues visualization."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import datetime
import dateutil
import pickle
import github_tools
import os
import sys
from subprocess import check_output

# TODO:
# confirm that local and API-gotten commits' dates are identical
#
# possibly use a database instead of pickling: https://github.com/pudo/dataset
# issue open duration should not be in recarray
# link plots
# (opendate, 1), (closedate, -1); cat; sort_by_date; cumsum(col2); plot
# same for PR
# use PyGithub's new "since" for getting fresh commits only
#
# Calculate average, stddev, max of time-to-fix, open time.
#
# other plots:
# % issues without label
# issue longest silent
# longest open issue
# most issues closed/opened per week/7day window
# % without any comment
# most bugs squashed

# Github/PyGithub objects are Capitalized!

# import times # module for saner time management.
# See http://nvie.com/posts/introducing-times/

###############################################################################
# CONFIGURATION
fetch = True  # fetch data from github or load from json-serialized file
# fetch=False
target_branch = 'master'

mpl.rc('axes', grid=True, axisbelow=True)
mpl.rc('grid', linestyle='-', color='lightgray')
mpl.rc('figure', dpi=90)
# -----------------------------------------------------------------------------
datefmt = "%Y-%m-%dT%H:%M:%SZ"  # 2012-05-19T00:28:09Z
event_datefmt = "%Y-%m-%d"
tmp = [['2008-09-04', '2008-09-09'],
       ['2011-01-10', '2011-01-14'],
       ['2012-02-20', '2012-02-27'],
       ['2013-08-08', '2013-08-14']]
OFEventTitles = ['OFLab Linz', 'DevCon Pittsburgh',
                 'DevCon Detroit', 'DevCon Yamaguchi']
OFEvents = [[datetime.datetime.strptime(x, event_datefmt) for x in y]
            for y in tmp]

pickle_dir = os.path.abspath('issue_stats_pickles')
autosave_dir = os.path.abspath('issue_stats_autosave')


def naive_dt(datetime):
    """
    Return a naive datetime.datetime object converted from a passed aware one.

    Enables comparison of aware datetimes from the local repo and the
    naive ones coming from PyGithub.
    """

    return datetime.astimezone(dateutil.tz.tzutc()).replace(tzinfo=None)


def annot_tags_events(axis, tags_recarray, events, event_titles):
    """Add tag and event annotations to a given axis"""

    for t in range(tags_recarray.shape[0]):
        axis.axvline(tags_recarray.date[t], color='y', alpha=0.5)
        plt.annotate(tags_recarray.name[t], xy=(tags_recarray.date[t], 0.90),
                     xycoords=("data", "axes fraction"), ha='right', va='top')

    for e in range(len(event_titles)):
        axis.axvspan(events[e][0], events[e][1], color='y', alpha=0.5)
        plt.annotate(event_titles[e], xy=(events[e][0], 0.97),
                     xycoords=("data", "axes fraction"), ha='right', va='top')

###############################################################################
# Fetch needed data
print('Fetching fresh data from Github')
Repo = github_tools.get_repo()

###############################################################################
print('Getting issues')
print('\nGithub shows ' + str(Repo.open_issues) + ' open issues.')
github_tools.log_traffic()  # initial call to establish baseline
issues_path = os.path.join(pickle_dir, 'Issues.pickle')
if os.path.isfile(issues_path):
    print('Loading issues from disk. Updating')
    with open(issues_path, 'rb') as fp:
        Issues = pickle.load(fp)
    last_update = max({v.updated_at for v in Issues.values()})
    print('Last updated at ' + str(last_update) + ' UTC')
    _issue_updates = Repo.get_issues(state='all', since=last_update)
    _counter = 0
    for i in _issue_updates:
        _counter += 1
        Issues[i.number] = i  # replace updated issues in local structure
    print(str(_counter) + ' issue(s) updated')
else:
    print('\nFetching issues from Github')
    Issues = dict()  # holds the PyGithub issues, indexed by number
    for i in Repo.get_issues(state='all'):
        #  i.update()  # to fetch whole contents
        # This takes one request per update(), and is very slow!
        # (15+ min and 10-20kB/s)
        # skipping this step takes 100 requests for 3000 issues, and 2min or so
        Issues[i.number] = i
    print('Issues received')

print('Creating issues recarray')
#    unicode strings as objects, otherwise string length is 0!
issues_dtype = [('number', int),
                ('state', object),
                ('created_at', object),
                ('closed_at', object),
                ('duration_open', object)]
#    create new, empty recarray:
issues_ra = np.recarray((0,), dtype=issues_dtype)
for i in Issues.values():
    issues_ra.resize(issues_ra.shape[0]+1)
    if i.closed_at:
        closedate = i.closed_at
    else:
        closedate = None
    entry = (i.number,
             i.state,
             i.created_at,
             i.closed_at,
             (closedate or datetime.datetime.now()) - i.created_at)
    issues_ra[-1] = entry
issues_ra.sort(order='number')
print('%s issues on record' % issues_ra.shape[0])
github_tools.log_traffic()

###############################################################################
print('\nGetting tags')
Tags = Repo.get_tags()
print('Creating tags recarray')
tags_dtype = [('date', object), ('name', object)]
tags_ra = np.recarray((0,), dtype=tags_dtype)
for t in Tags:
    tags_ra.resize(tags_ra.shape[0]+1)
    tags_ra[-1] = (t.commit.commit.committer.date, t.name)
print('%s tags available' % tags_ra.shape[0])
github_tools.log_traffic()

###############################################################################
print('\nGetting commits')
commits_dtype = [('sha', object),
                 ('commit_date', object),
                 ('author_date', object)]
commits_ra = np.recarray((0,), dtype=commits_dtype)

repopath = github_tools.local_repo_location()
if repopath:
    print('Getting commit data from local repository...')
    # check for correct branch
    if check_output(['git', 'symbolic-ref', '--short', 'HEAD'],
                    cwd=repopath,
                    universal_newlines=True).rstrip() != target_branch:
        print('ERROR: Please check out the branch ' +
              target_branch + ' first.')
        sys.exit(1)
    # check if up-to-date commit is checked out
    current_sha = Repo.get_branch(target_branch).commit.sha
    if check_output(['git', 'rev-parse', '--verify', 'HEAD'],
                    cwd=repopath,
                    universal_newlines=True).rstrip() != current_sha:
        print('ERROR: Please sync with the remote repository. ' +
              'The current online commit is ' + current_sha)
        sys.exit(1)
    # get commit list
    _out = check_output(['git', '--no-pager', 'log', target_branch,
                         '--pretty=format:"%h  %ci  %ai  %p"'],
                        cwd=repopath,
                        universal_newlines=True)
    _outlist = [o.strip('"') for o in _out.split(sep='\n')]
    for l in _outlist:
        # split into sha, committer date, author date, parents
        _temp = l.split(sep='  ')
        commits_ra.resize(commits_ra.shape[0]+1)
        # TODO: Add parents to recarray
        commits_ra[-1] = (_temp[0],
                          naive_dt(dateutil.parser.parse(_temp[1])),
                          naive_dt(dateutil.parser.parse(_temp[2])))
    print('Done')
else:
    print('No local repository specified. Getting commits from Github')
    Commits = Repo.get_commits()
    for c in Commits:
        commits_ra.resize(commits_ra.shape[0]+1)
        commits_ra[-1] = (c.sha,
                          c.commit.committer.date,
                          c.commit.author.date)
    print('%s commits received' % commits_ra.shape[0])
    github_tools.log_traffic()

###############################################################################
print('\nProcessing objects')

# one row of dates, one row of indices, +1 for opening, -1 for closing
open_issue_count = np.vstack((issues_ra.created_at,
                              np.ones((len(issues_ra.created_at)))
                              ))
issue_close_dates = issues_ra.closed_at[issues_ra.state == 'closed']
_closed_issues = np.vstack((issue_close_dates,
                            -1*np.ones((len(issue_close_dates)))
                            ))
open_issue_count = np.hstack((open_issue_count, _closed_issues)).T

open_issue_count = open_issue_count[open_issue_count[:, 0].argsort()]
open_issue_count = np.column_stack((open_issue_count,
                                    np.cumsum(open_issue_count[:, 1], axis=0)))
# alternatively, use np.newaxis to get a proper 2D array
# print str(np.shape(open_issue_count))

xbegin = min([min(commits_ra.author_date), min(issues_ra.created_at)])
xend = datetime.datetime.utcnow()
print("Data range: %s days" % str((xend-xbegin).days))
bin_rrule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY,
                                 dtstart=xbegin,
                                 byweekday=dateutil.rrule.MO)
bin_edges = mpl.dates.date2num([xbegin] +
                               bin_rrule.between(xbegin, xend, inc=False) +
                               [xend])

###############################################################################
# Pickling of data structures
with open(issues_path, 'wb') as fp:
    pickle.dump(Issues, fp)

###############################################################################
# Plot figure
fig = plt.figure(figsize=(380/25.4, 200/25.4))
ax = fig.add_subplot(211)
plt.title('OF issue tracker statistics - created ' + str(xend.date()))

annot_tags_events(ax, tags_ra, OFEvents, OFEventTitles)
ax.plot(open_issue_count[:, 0], open_issue_count[:, 2],
        label='open issues', color='k', alpha=0.8)
ax.hist([mpl.dates.date2num(issues_ra.created_at),
         mpl.dates.date2num(issues_ra.closed_at[issues_ra.state == 'closed'])],
        histtype='barstacked',
        bins=bin_edges,
        label=['created issues', 'closed issues'],
        color=['red', 'green'],
        alpha=0.8)

ax.legend(loc='center left')
locator = mpl.dates.AutoDateLocator(maxticks=15)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(mpl.dates.AutoDateFormatter(locator))
ax.xaxis.grid(False)
ax.set_xlim(left=xbegin)
ax.tick_params(axis='x', direction='out')

# -----------------------------------------------------------------------------
ax2 = fig.add_subplot(212, sharex=ax)
plt.title('OF commit statistics')
annot_tags_events(ax2, tags_ra, OFEvents, OFEventTitles)
ax2.hist(mpl.dates.date2num(commits_ra.author_date),
         bins=bin_edges,
         label=(target_branch + ' commits authored'),
         color='blue',
         alpha=0.5)
ax2.legend(loc='center left')
ax2.xaxis.set_major_locator(locator)
ax2.xaxis.set_major_formatter(mpl.dates.AutoDateFormatter(locator))
ax2.xaxis.grid(False)
ax2.set_xlim(left=xbegin)
ax2.tick_params(axis='x', direction='out')

fig.autofmt_xdate()
plt.tight_layout()

plt.show()
fig.savefig(os.path.join(autosave_dir, 'OF_repo_viz_'+str(xend.date())+'.png'))
print('\nFinished!')
###############################################################################
