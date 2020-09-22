# sltxinst

## Short overview

`sltxinst` is a simple (python 3.5+) script, i've written for *my own purposes* (LaTeX).
It uses `sltx-dep.yml` files to track my latex dependencies over various repositories and installs them on the host-system.
I use it only under linux, with texlive installed, but it should work for other os too.
You can configure the installer for your host-system using the `sltx-config.yml` or supplying on when installing.

Todos:

* add .sltx-src.yml or some similar file so that the repo itself can determine what it should serve? -- maybe allow different "sets"?
  
* Update functionality
  