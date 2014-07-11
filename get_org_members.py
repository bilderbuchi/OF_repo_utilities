#!/usr/bin/env python3

"""Print a list of organization team members. Token needs read:org scope."""

import github_tools

G = github_tools.get_github_instance()
org = G.get_organization('openframeworks')
teams = org.get_teams()

for t in teams:
    if 'devs' not in t.name:
        print(t.name + ':')
        members = t.get_members()
        for m in members:
            if m.name:
                name = m.name
            else:
                name = ''
            print('@' + m.login + ' ' + name)
        print('')
