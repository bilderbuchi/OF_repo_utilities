#!/usr/bin/env python3

"""Print the percentage of unmergeable PRs and some associated stats."""

import github_tools

Repo = github_tools.get_repo()
merge_true = 0
merge_false = 0
nr_prs = 0

pulls = Repo.get_pulls('open')
for p in pulls:
    nr_prs += 1
    print("nr " + str(p.number) + ", mergeable:" + str(p.mergeable))
    if p.mergeable:
        merge_true += 1
    else:
        merge_false += 1

# sanity check
assert(nr_prs == (merge_true + merge_false))

print('Open PRs: ' + str(nr_prs) +
      '\nMergeable: ' + str(merge_true) +
      '\nUnmergeable: ' + str(merge_false) +
      '\nPercentage unmergeable: ' +
      '%.2f' % (100.0 * merge_false / nr_prs))
