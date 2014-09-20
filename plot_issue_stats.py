#!/usr/bin/env python3
"""Main script for openFrameworks Github issues visualization."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import datetime
import dateutil
import pickle
import github_tools
import os
import sys
from subprocess import check_output
from operator import itemgetter

# TODO:
# possibly use a database instead of pickling: https://github.com/pudo/dataset
# link plots
# Calculate average, stddev, max of time-to-fix, open time.
# other plots:
# % issues without label
# issue longest silent
# longest open issue
# most issues closed/opened per week/7day window
# % without any comment
# most bugs squashed


def naive_dt(aware_datetime):
    """
    Return a naive datetime.datetime object converted from a passed aware one.

    Enables comparison of aware datetimes from the local repo and the
    naive ones coming from PyGithub.
    """

    return aware_datetime.astimezone(dateutil.tz.tzutc()).replace(tzinfo=None)


def annot_tags_events(axis, tag_list, events, event_titles):
    """Add tag and event annotations to a given axis"""

    for _t in tag_list:
        axis.axvline(_t['date'], color='y', alpha=0.5)
        plt.annotate(_t['name'], xy=(_t['date'], 0.90),
                     xycoords=("data", "axes fraction"), ha='right', va='top')

    for e in range(len(event_titles)):
        axis.axvspan(events[e][0], events[e][1], color='y', alpha=0.5)
        plt.annotate(event_titles[e], xy=(events[e][0], 0.97),
                     xycoords=("data", "axes fraction"), ha='right', va='top')


def main():
    """Main function for plot_issue_stats"""
    ###########################################################################
    # CONFIGURATION
    target_branch = 'master'

    mpl.rc('axes', grid=True, axisbelow=True)
    mpl.rc('grid', linestyle='-', color='lightgray')
    mpl.rc('figure', dpi=90)
    # -------------------------------------------------------------------------
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

    ###########################################################################
    # Fetch needed data
    print('Fetching fresh data from Github')
    Repo = github_tools.get_repo()

    ###########################################################################
    print('\nGetting issues')
    print('Github shows ' + str(Repo.open_issues) + ' open issues.')
    github_tools.log_traffic()  # initial call to establish baseline
    issues_path = os.path.join(pickle_dir, 'Issues.pickle')
    if os.path.isfile(issues_path):
        print('Loading issues from disk. Updating...')
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
            # skipping this step takes 100 requests for 3000 issues and ca 2min
            Issues[i.number] = i
        print('Issues received')

    print('Creating processed issue list')
    issue_list = []
    for i in Issues.values():
        if i.closed_at:
            _closed = i.closed_at
        else:
            _closed = None
        _duration = (i.closed_at or datetime.datetime.now()) - i.created_at
        issue_list.append({'number': i.number,
                           'state': i.state,
                           'created_at': i.created_at,
                           'closed_at': _closed,
                           'duration_open': _duration})
    issue_list.sort(key=itemgetter('number'))
    print('%s issues on record' % len(issue_list))

    github_tools.log_traffic()

    ###########################################################################
    print('\nGetting tags')
    Tags = Repo.get_tags()
    print('Creating tags list')
    tags_list = []
    for t in Tags:
        tags_list.append({'date': t.commit.commit.committer.date,
                          'name': t.name})
    github_tools.log_traffic()

    ###########################################################################
    print('\nGetting commits')
    commits_list = []

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
            _parse = dateutil.parser.parse
            # TODO: add parents to data structure
            commits_list.append({'sha': _temp[0],
                                 'committer_date': naive_dt(_parse(_temp[1])),
                                 'author_date': naive_dt(_parse(_temp[2]))})
        print('%s commits on record' % len(commits_list))
        print('Done')
    else:
        print('No local repository specified. Getting commits from Github')
        Commits = Repo.get_commits()
        for c in Commits:
            commits_list.append({'sha': c.sha,
                                 'committer_date': c.commit.committer.date,
                                 'author_date': c.commit.author.date})
        print('%s commits received' % len(commits_list))
        github_tools.log_traffic()

    ###########################################################################
    print('\nProcessing objects')

    # one row of dates, one row of indices, +1 for opening, -1 for closing
    open_issue_count = []
    for i in issue_list:
        open_issue_count.append({'date': i['created_at'],
                                 'status_change': 1})
        if i['closed_at']:
            open_issue_count.append({'date': i['closed_at'],
                                     'status_change': -1})
    open_issue_count.sort(key=itemgetter('date'))
    _sum = 0
    for i in open_issue_count:
        _sum += i['status_change']
        i['open_issues'] = _sum

    xbegin = min([min([x['author_date'] for x in commits_list]),
                  min([x['date'] for x in open_issue_count])])
    xend = datetime.datetime.utcnow()
    print("Data range: %s days" % str((xend-xbegin).days))
    bin_rrule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY,
                                     dtstart=xbegin,
                                     byweekday=dateutil.rrule.MO)
    bin_edges = mpl.dates.date2num([xbegin] +
                                   bin_rrule.between(xbegin, xend, inc=False) +
                                   [xend])

    ###########################################################################
    # Pickling of data structures
    with open(issues_path, 'wb') as fp:
        pickle.dump(Issues, fp)

    ###########################################################################
    print('Plotting figure')
    fig = plt.figure(figsize=(380/25.4, 200/25.4))
    ax = fig.add_subplot(211)
    plt.title('OF issue tracker statistics - created ' + str(xend.date()))

    annot_tags_events(ax, tags_list, OFEvents, OFEventTitles)
    ax.plot([x['date'] for x in open_issue_count],
            [x['open_issues'] for x in open_issue_count],
            label='open issues', color='k', alpha=0.8)
    _closed_issue_dates = [x['closed_at'] for x in issue_list
                           if x['state'] == 'closed']
    ax.hist([mpl.dates.date2num([x['created_at'] for x in issue_list]),
             mpl.dates.date2num(_closed_issue_dates)],
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

    # -------------------------------------------------------------------------
    ax2 = fig.add_subplot(212, sharex=ax)
    plt.title('OF commit statistics')
    annot_tags_events(ax2, tags_list, OFEvents, OFEventTitles)
    ax2.hist(mpl.dates.date2num([x['author_date'] for x in commits_list]),
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
    fig.savefig(os.path.join(autosave_dir, 'OF_repo_viz_' + str(xend.date()) +
                             '.png'))
    print('\nFinished!')
    ###########################################################################

if __name__ == '__main__':
    main()
