# OF repo utilities
A collection of utility scripts that I use when working with the [openFrameworks](www.openframeworks.cc) Github and Git repositories.

Currently requires Python 3 to run.

## Github token
This collection of scripts needs a file (default name `github_token.txt`) containing only a [Github personal API token](https://github.com/blog/1509-personal-api-tokens) for authenticating with the Github API.  
Only the public access scope is needed, except for `get_org_members.py`, which also needs the `read:org` scope.

## Local repository access
For the `plot_issue_stats` script, optionally, the path to a local copy of the Github repository can be supplied in a file named `local_repo_location.txt`.
This way, commit data is aquired locally instead of with the Github API, saving loads of traffic and time during execution.

## Required packages
* [PyGithub](https://github.com/jacquev6/PyGithub)
* [Matplotlib](http://matplotlib.org/) (for `plot_issue_stats`)
* [Numpy](http://www.numpy.org/) (for `plot_issue_stats`)
* [dateutil](https://pypi.python.org/pypi/python-dateutil) (for `plot_issue_stats`)

## License
MIT License, see LICENSE.md
