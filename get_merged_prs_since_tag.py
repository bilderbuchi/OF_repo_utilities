#!/usr/bin/env python3

"""Get a markdown-formatted list of PRs merged since a certain tag."""

import github_tools

Repo = github_tools.get_repo()

# TODO: implement getting date from repo tag./
tagname = '0.8.1'
tags = Repo.get_tags()
for t in tags:
    if t.name == tagname:
        startdate = t.commit.commit.committer.date
        print('Tag date: ' + str(startdate))

pulls = Repo.get_pulls('closed')
user_length = 0
for p in pulls:
    if (p.closed_at > startdate) and p.merged:
        user_length = max(user_length, len(p.user.login))
format_string = '{:<' + str(user_length) + '}'

for p in pulls:
    if (p.closed_at > startdate) and p.merged:
        print("* [Nr " + str(p.number) + "]( "
              + str(p.html_url) + " ) by " + format_string.format(p.user.login)
              + ': ' + str(p.title))
