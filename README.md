# OF repo utilities
A collection of utility scripts that I use when working with the [openFrameworks](www.openframeworks.cc) Github and Git repositories.

Currently requires Python 3 to run.

## Github token
This collection of scripts needs a file (default name `github_token.txt`) containing only a [Github personal API token](https://github.com/blog/1509-personal-api-tokens) for authenticating with the Github API.  
Only the public access scope is needed, except for `get_org_members.py`, which also needs the `read:org` scope.

## Required packages
* [PyGithub](https://github.com/jacquev6/PyGithub)

## License
MIT License, see LICENSE.md
