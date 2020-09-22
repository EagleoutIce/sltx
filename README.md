[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/) [![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/EagleoutIce/sltx/graphs/commit-activity) [![PyPI version shields.io](https://img.shields.io/pypi/v/sltx.svg)](https://pypi.python.org/pypi/sltx/)
[![Generic badge](https://img.shields.io/badge/Status-WIP-purple.svg)](https://github.com/EagleoutIce/sltx)

# sltx 0.1.x

1. [Short overview](#short-overview)
2. [How tos'](#how-tos)
   1. [How to get](#how-to-get)
   2. [How to run](#how-to-run)
3. [Todos](#todos)

## Short overview

`sltx` is a simple (python 3.5+) script, i've written for *my own purposes* (LaTeX).
It uses `sltx-dep.yml` files to track my latex dependencies over various repositories and installs them on the host-system.
I use it only under linux, with texlive installed, but it should work for other os too.
You can configure the installer for your host-system using the `sltx-config.yml` or supply it while installing.

## How tos'

### How to get

The script including the Package `sltxpkg` is available with [pypi/sltx](https://pypi.org/project/sltx/)
So simply install it like any other Python package with `sltx` with pip:

```bash
pip install sltx
```

(You can use `pip3` as well)

Afterwards `sltx` should be available as a normal script! Afterwards you can
updates with `pip` and the `--upgrade`-flag.

### How to run

Just run `sltx` or `sltx -h` to get the help menu.
If you want to install dependencies from a file like `dep.yml` run:

```bash
sltx -d dep.yml
```

If you have your own configuration, lets say it is name "config.yml" add `-c config.yml`.

If you want to generate a *github workflow* just type `sltx -g`.

## Todos

* add .sltx-src.yml or some similar file so that the repo itself can determine what it should serve? -- maybe allow different "sets"?
  
* Update functionality
  