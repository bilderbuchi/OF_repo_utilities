#!/usr/bin/env python3

"""Get a markdown-formatted list of PRs merged since a certain tag."""

import github_tools

Repo = github_tools.get_repo()

# TODO: implement getting date from repo tag.
tagname = '0.8.1'
tags = Repo.get_tags()
for t in tags:
    if t.name == tagname:
        startdate = t.commit.commit.committer.date
        print('Selected tag ' + tagname + ', date: ' + str(startdate))

print('Fetching data...\n\n')
pulls = Repo.get_pulls('closed')
results = []
for p in pulls:
    if (p.closed_at > startdate) and p.merged:
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
