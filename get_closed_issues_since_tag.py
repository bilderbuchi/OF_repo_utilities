#!/usr/bin/env python3

"""Print a list of issues closed since a certain tag.

The tag name can be given as argument. If none was given, choose latest tag.
"""

import github_tools
import sys

if len(sys.argv) == 2:
    tagname = sys.argv[1]
else:
    tagname = ''

repo = github_tools.get_repo()
tag = github_tools.validate_tagname(repo, tagname)
closed_issues = repo.get_issues(state='closed', since=tag['date'])
print('nr.  close_time          PR?   closed_by title')

for c in closed_issues:
    if c.closed_at > tag['date']:
        if c.pull_request:
            PR = 'wasPR'
        else:
            PR = '     '
        print(c.number, c.closed_at.isoformat(), PR,
              str(c.closed_by.login) + '\t', str(c.title))
