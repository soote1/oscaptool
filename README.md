Table of Contents
=======================

* [What is oscaptool?](#what-is-oscaptool)
* [Design](#design)
* [Installation Instructions](#installation-instructions)
* [Running oscaptool](#running-bettingtool)
* [Testing](#testing)
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

Design
------
oscaptool is a flexible multicommand cli tool. The current implementation allows any developer to add new commands and related workflows
by providing new settings in the app's configuration file without changing the current code base. In order to provide these features, oscaptool
uses four classes:
* **Client**: a class to manage the execution of the main operations such as arguments parsing and workflow execution.
* **ArgsParser**: a class that uses the argparse module to provide argument parsing functionality. The logic to build the parsers from the argparse module
can be defined in the app's configuration file.
* **ActionManager**: a manager class that executes a workflow (set of actions in sequential order). Several workflows can be defined in the app's configuration file.
* **Action**: a class that performs a specific logic such as printing to the stdout, fetching the scan history from the file system, build a command string, execute a command, and so on.  
Here is a chart illustrating the basic workflow executed by the oscaptool.
![Alt text](docs/oscaptool_flow.png?raw=true "oscaptool_workflow")

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
Once the virtualenv is running, you will be able to find the oscaptool command

Running oscaptool
------
oscaptool depends on two configuration files:
* **logging.conf**: contains settings for the logging module.
* **config.json**: contains settings for building the args parser and action manager objects.

Make sure that both files are filled propperly before running the application.

There are multiple ways to run the oscaptool command depending on the feature you want to use. 
Before start using the cli tool, run the following command to identify the available options:
```bash
oscaptool --help
```
Testing
------
Unit tests are under development. Meanwhile, you can run the following commands to exercise the features:  
* Perform basic scan
```bash
oscaptool scan xccdf 1 stig /tmp/ssg-results.xml /usr/share/xml/scap/ssg/content/ssg-ol7-cpe-dictionary.xml /usr/share/xml/scap/ssg/content/ssg-ol7-xccdf.xml
```
* Show scan history
```bash
oscaptool show
```
* Show scan result
```bash
oscaptool show --scan-id file_name_without_txt_extension
```
* Compare two scan results
```bash
oscaptool comp file_name_1_without_txt_extension file_name_2_without_txt_extension
```
Licensing
------
The code in this project is released under the [MIT License](LICENSE).