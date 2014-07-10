#!/usr/bin/env python3

"""Get a markdown-formatted list of PRs merged since a certain tag.

The tag name can be given as argument. If none was given, choose latest tag.
"""

import github_tools
import sys

if len(sys.argv) == 2:
    tagname = sys.argv[1]
else:
    tagname = ''

Repo = github_tools.get_repo()
print('Fetching tags...')
tags = Repo.get_tags()
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

print('Fetching data...\n\n')
pulls = Repo.get_pulls('closed')
results = []
for p in pulls:
    if (p.closed_at > tag['date']) and p.merged:
        results.append({'login': p.user.login,
                        'number': p.number,
                        'url': p.html_url,
                        'title': p.title})

user_maxlength = max([len(entry['login']) for entry in results])
format_string = '{:<' + str(user_maxlength) + '}'

for r in results:
    print("* [Nr " + str(r['number']) + "]( "
          + str(r['url']) + " ) by "
          + format_string.format(r['login'])
          + ': ' + str(r['title']))
