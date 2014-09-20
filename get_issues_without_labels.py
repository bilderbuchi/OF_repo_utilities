#!/usr/bin/env python3

""" List unlabeled Github issues, optionally open them in a browser."""

import github_tools


def main():
    """Main function for get_issues_without_labels"""
    repo = github_tools.get_repo()
    list_of_issue_urls = []
    issues = repo.get_issues(state='open')
    print('List of open issues without labels:')
    for i in issues:
        if (i.labels == []) and (i.pull_request is None):
            list_of_issue_urls.append(i.html_url)
            print(i.number)

    print('\n')
    github_tools.open_in_browser(list_of_issue_urls)

if __name__ == '__main__':
    main()
