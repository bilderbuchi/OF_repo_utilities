#!/usr/bin/env python3

"""Print a list of organization team members. Token needs read:org scope."""

import github_tools


def main():
    """Main function of get_org_members"""
    gh_instance = github_tools.get_github_instance()
    org = gh_instance.get_organization('openframeworks')
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

if __name__ == '__main__':
    main()
