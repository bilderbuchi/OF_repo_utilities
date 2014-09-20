#!/usr/bin/env python3

"""Get a markdown-formatted list of PRs merged since a certain tag.

The tag name can be given as argument. If none was given, choose latest tag.
"""

# TODO: Why is this script so bandwidth-intensive?

import github_tools
import sys


def main(args):
    """Main function of get_merged_prs_since_tag"""
    if len(args) == 2:
        tagname = args[1]
    else:
        tagname = ''
    repo = github_tools.get_repo()
    tag = github_tools.validate_tagname(repo, tagname)
    print('Fetching data...\n\n')
    pulls = repo.get_pulls(state='closed')
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
        print("* [Nr " + str(r['number']) + "]( " + str(r['url']) + " ) by " +
              format_string.format(r['login']) + ': ' + str(r['title']))

if __name__ == '__main__':
    main(sys.argv)
