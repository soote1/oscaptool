Table of Contents
=======================

* [What is oscaptool?](#what-is-oscaptool)
* [Installation Instructions](#installation-instructions)
* [Running oscaptool](#running-bettingtool)
* [Testing](#testing)
* [Community and Contributing](#community-and-contributing)
* [Directory Structure](#directory-structure)
* [Licensing](#licensing)

---

What is oscaptool?
------
oscaptool is a CLI tool for regular "openscap" scans of the Oracle Linux 7 system.

The CLI provides the following features:

* Execute a scan and print the scan result in the output.
* List history of executed scans printing scan ids.
* Print a scan result by any scan id available from the history.
* Compare two scan results available from the history by scan ids. (id/total/passed/failed)

Installation Instructions
------
Run the following commands to create the dev/test environment:
```bash
docker-compose up --build
docker-compose run oscaptool sh
```
Once the environment has been created, run the following command to start the virtualenv:
```bash
pipenv shell
```
Once the virtualenv is running, you will be able to run the oscaptool command

Running oscaptool
------
There are multiple ways to run the oscaptool command depending on the feature you want to use. 
Before start using the cli tool, run the following command to identify the available options:
```bash
oscaptool --help
```

Testing
------
TBD

Licensing
------
The code in this project is released under the [MIT License](LICENSE).