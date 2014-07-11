#!/usr/bin/env python3

"""Print the percentage of unmergeable PRs and some associated stats."""

import github_tools
from time import sleep

Repo = github_tools.get_repo()
merge_true = 0
merge_false = 0
nr_prs = 0
unmergeable_urls = []

pulls = Repo.get_pulls('open')
for p in pulls:
    nr_prs += 1
    # TODO: Workaround for https://github.com/jacquev6/PyGithub/issues/256
    while p.mergeable is None:
        print('Uncached mergeable state enountered for ' + str(p.number))
        sleep(1)
        p.update()
    print("nr " + str(p.number) + ", mergeable:" + str(p.mergeable))
    if p.mergeable:
        merge_true += 1
    else:
        merge_false += 1
        unmergeable_urls.append(p.html_url)

# sanity check
assert(nr_prs == (merge_true + merge_false))

print('Open PRs: ' + str(nr_prs) +
      '\nMergeable: ' + str(merge_true) +
      '\nUnmergeable: ' + str(merge_false) +
      '\nPercentage unmergeable: ' +
      '%.2f' % (100.0 * merge_false / nr_prs))

github_tools.open_in_browser(unmergeable_urls)
