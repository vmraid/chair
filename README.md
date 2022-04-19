<div align="center">
	<img src="https://github.com/vmraid/design/raw/master/logos/png/chair-logo.png" height="128">
	<h2>Chair</h2>
</div>

Chair is a command-line utility that helps you to install, update, and manage multiple sites for VMRaid/ERPAdda applications on [*nix systems](https://en.wikipedia.org/wiki/Unix-like) for development and production.

<div align="center">
	<a target="_blank" href="https://www.python.org/downloads/" title="Python version">
		<img src="https://img.shields.io/badge/python-%3E=_3.6-green.svg">
	</a>
	<a target="_blank" href="https://app.travis-ci.com/github/vmraid/chair" title="CI Status">
		<img src="https://app.travis-ci.com/vmraid/chair.svg?branch=develop">
	</a>
	<a target="_blank" href="https://pypi.org/project/vmraid-chair" title="PyPI Version">
		<img src="https://badge.fury.io/py/vmraid-chair.svg" alt="PyPI version">
	</a>
	<a target="_blank" title="Platform Compatibility">
		<img src="https://img.shields.io/badge/platform-linux%20%7C%20osx-blue">
	</a>
	<a target="_blank" href="https://app.fossa.com/projects/git%2Bgithub.com%2Fvmraid%2Fchair?ref=badge_shield" title="FOSSA Status">
		<img src="https://app.fossa.com/api/projects/git%2Bgithub.com%2Fvmraid%2Fchair.svg?type=shield">
	</a>
	<a target="_blank" href="#LICENSE" title="License: GPLv3">
		<img src="https://img.shields.io/badge/License-GPLv3-blue.svg">
	</a>
</div>

## Table of Contents

 - [Installation](#installation)
	- [Containerized Installation](#containerized-installation)
	- [Easy Install Script](#easy-install-script)
	- [Manual Installation](#manual-installation)
 - [Usage](#basic-usage)
 - [Custom Chair commands](#custom-chair-commands)
 - [Chair Manager](#chair-manager)
 - [Guides](#guides)
 - [Resources](#resources)
 - [Development](#development)
 - [Releases](#releases)
 - [License](#license)


## Installation

A typical chair setup provides two types of environments &mdash; Development and Production.

The setup for each of these installations can be achieved in multiple ways:

 - [Containerized Installation](#containerized-installation)
 - [Easy Install Script](#easy-install-script)
 - [Manual Installation](#manual-installation)

We recommend using either the Docker Installation or the Easy Install Script to setup a Production Environment. For Development, you may choose either of the three methods to setup an instance.

Otherwise, if you are looking to evaluate ERPAdda, you can also download the [Virtual Machine Image](https://erpadda.com/download) or register for [a free trial on erpadda.com](https://erpadda.com/pricing).


### Containerized Installation

A VMRaid/ERPAdda instance can be setup and replicated easily using [Docker](https://docker.com). The officially supported Docker installation can be used to setup either of both Development and Production environments.

To setup either of the environments, you will need to clone the official docker repository:

```sh
$ git clone https://github.com/vmraid/vmraid_docker.git
$ cd vmraid_docker
```

A quick setup guide for both the environments can be found below. For more details, check out the [VMRaid/ERPAdda Docker Repository](https://github.com/vmraid/vmraid_docker).

### Easy Install Script

The Easy Install script should get you going with a VMRaid/ERPAdda setup with minimal manual intervention and effort. Since there are a lot of configurations being automatically setup, we recommend executing this script on a fresh server.

**Note:** This script works only on GNU/Linux based server distributions, and has been designed and tested to work on Ubuntu 16.04+, CentOS 7+, and Debian-based systems.

> This script installs Version 12 by default. It is untested with Version 13 and above. Containerized or manual installs are recommended for newer setups.

#### Prerequisites

You need to install the following packages for the script to run:

 - ##### Ubuntu and Debian-based Distributions:

	```sh
	$ apt install python3-minimal build-essential python3-setuptools
	```

 - ##### CentOS and other RPM Distributions:

	```sh
	$ dnf groupinstall "Development Tools"
	$ dnf install python3
	```

#### Setup

Download the Easy Install script and execute it:

```sh
$ wget https://raw.githubusercontent.com/vmraid/chair/develop/install.py
$ python3 install.py --production
```

The script should then prompt you for the MySQL root password and an Administrator password for the VMRaid/ERPAdda instance, which will then be saved under `$HOME/passwords.txt` of the user used to setup the instance. This script will then install the required stack, setup chair and a default ERPAdda instance.

When the setup is complete, you will be able to access the system at `http://<your-server-ip>`, wherein you can use the administrator password to login.

#### Troubleshooting

In case the setup fails, the log file is saved under `/tmp/logs/install_chair.log`. You may then:

 - Create an Issue in this repository with the log file attached.
 - Search for an existing issue or post the log file on the [VMRaid/ERPAdda Discuss Forum](https://discuss.erpadda.com/c/chair) with the tag `installation_problem` under "Install/Update" category.

For more information and advanced setup instructions, check out the [Easy Install Documentation](https://github.com/vmraid/chair/blob/develop/docs/easy_install.md).


### Manual Installation

Some might want to manually setup a chair instance locally for development. To quickly get started on installing chair the hard way, you can follow the guide on [Installing Chair and the VMRaid Framework](https://vmraid.io/docs/user/en/installation).

You'll have to set up the system dependencies required for setting up a VMRaid Environment. Checkout [docs/installation](https://github.com/vmraid/chair/blob/develop/docs/installation.md) for more information on this. If you've already set up, install chair via pip:


```sh
$ pip install vmraid-chair
```

For more extensive distribution-dependent documentation, check out the following guides:

 - [Hitchhiker's Guide to Installing VMRaid on Linux](https://github.com/vmraid/vmraid/wiki/The-Hitchhiker%27s-Guide-to-Installing-VMRaid-on-Linux)
 - [Hitchhiker's Guide to Installing VMRaid on MacOS](https://github.com/vmraid/chair/wiki/Setting-up-a-Mac-for-VMRaid-ERPAdda-Development)


## Basic Usage

**Note:** Apart from `chair init`, all other chair commands are expected to be run in the respective chair directory.

 * Create a new chair:

	```sh
	$ chair init [chair-name]
	```

 * Add a site under current chair:

	```sh
	$ chair new-site [site-name]
	```
	- **Optional**: If the database for the site does not reside on localhost or listens on a custom port, you can use the flags `--db-host` to set a custom host and/or `--db-port` to set a custom port.

		```sh
		$ chair new-site [site-name] --db-host [custom-db-host-ip] --db-port [custom-db-port]
		```

 * Download and add applications to chair:

	```sh
	$ chair get-app [app-name] [app-link]
	```

 * Install apps on a particular site

	```sh
	$ chair --site [site-name] install-app [app-name]
	```

 * Start chair (only for development)

	```sh
	$ chair start
	```

 * Show chair help:

	```sh
	$ chair --help
	```


For more in-depth information on commands and their usage, follow [Commands and Usage](https://github.com/vmraid/chair/blob/develop/docs/commands_and_usage.md). As for a consolidated list of chair commands, check out [Chair Usage](https://github.com/vmraid/chair/blob/develop/docs/chair_usage.md).


## Custom Chair Commands

If you wish to extend the capabilities of chair with your own custom VMRaid Application, you may follow [Adding Custom Chair Commands](https://github.com/vmraid/chair/blob/develop/docs/chair_custom_cmd.md).


## Chair Manager

[Chair Manager](https://github.com/vmraid/chair_manager) is a GUI frontend for Chair with the same functionalties. You can install it by executing the following command:

```sh
$ chair setup manager
```

 - **Note:** This will create a new site to setup Chair Manager, if you want to set it up on an existing site, run the following commands:

	```sh
	$ chair get-app https://github.com/vmraid/chair_manager.git
	$ chair --site <sitename> install-app chair_manager
	```


## Guides

- [Configuring HTTPS](https://vmraid.io/docs/user/en/chair/guides/configuring-https.html)
- [Using Let's Encrypt to setup HTTPS](https://vmraid.io/docs/user/en/chair/guides/lets-encrypt-ssl-setup.html)
- [Diagnosing the Scheduler](https://vmraid.io/docs/user/en/chair/guides/diagnosing-the-scheduler.html)
- [Change Hostname](https://vmraid.io/docs/user/en/chair/guides/adding-custom-domains)
- [Manual Setup](https://vmraid.io/docs/user/en/chair/guides/manual-setup.html)
- [Setup Production](https://vmraid.io/docs/user/en/chair/guides/setup-production.html)
- [Setup Multitenancy](https://vmraid.io/docs/user/en/chair/guides/setup-multitenancy.html)
- [Stopping Production](https://github.com/vmraid/chair/wiki/Stopping-Production-and-starting-Development)

For an exhaustive list of guides, check out [Chair Guides](https://vmraid.io/docs/user/en/chair/guides).


## Resources

- [Chair Commands Cheat Sheet](https://vmraid.io/docs/user/en/chair/resources/chair-commands-cheatsheet.html)
- [Background Services](https://vmraid.io/docs/user/en/chair/resources/background-services.html)
- [Chair Procfile](https://vmraid.io/docs/user/en/chair/resources/chair-procfile.html)

For an exhaustive list of resources, check out [Chair Resources](https://vmraid.io/docs/user/en/chair/resources).


## Development

To contribute and develop on the chair CLI tool, clone this repo and create an editable install. In editable mode, you may get the following warning everytime you run a chair command:

	WARN: chair is installed in editable mode!

	This is not the recommended mode of installation for production. Instead, install the package from PyPI with: `pip install vmraid-chair`


```sh
$ git clone https://github.com/vmraid/chair ~/chair-repo
$ pip3 install -e ~/chair-repo
$ chair src
/Users/vmraid/chair-repo
```

To clear up the editable install and switch to a stable version of chair, uninstall via pip and delete the corresponding egg file from the python path.


```sh
# Delete chair installed in editable install
$ rm -r $(find ~ -name '*.egg-info')
$ pip3 uninstall vmraid-chair

# Install latest released version of chair
$ pip3 install -U vmraid-chair
```

To confirm the switch, check the output of `chair src`. It should change from something like `$HOME/chair-repo` to `/usr/local/lib/python3.6/dist-packages` and stop the editable install warnings from getting triggered at every command.


## Releases

Chair's version information can be accessed via `chair.VERSION` in the package's __init__.py file. Eversince the v5.0 release, we've started publishing releases on GitHub, and PyPI.

GitHub: https://github.com/vmraid/chair/releases

PyPI: https://pypi.org/project/vmraid-chair


From v5.3.0, we partially automated the release process using [@semantic-release](.github/workflows/release.yml). Under this new pipeline, we do the following steps to make a release:

1. Merge `develop` into the `staging` branch
1. Merge `staging` into the latest stable branch, which is `v5.x` at this point.

This triggers a GitHub Action job that generates a bump commit, drafts and generates a GitHub release, builds a Python package and publishes it to PyPI.

The intermediate `staging` branch exists to mediate the `chair.VERSION` conflict that would arise while merging `develop` and stable. On develop, the version has to be manually updated (for major release changes). The version tag plays a role in deciding when checks have to be made for new Chair releases.

> Note: We may want to kill the convention of separate branches for different version releases of Chair. We don't need to maintain this the way we do for VMRaid & ERPAdda. A single branch named `stable` would sustain.

## License

This repository has been released under the [GNU GPLv3 License](LICENSE).
