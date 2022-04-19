# chair CLI Usage

This may not be known to a lot of people but half the chair commands we're used to, exist in the VMRaid Framework and not in chair directly. Those commands generally are the `--site` commands. This page is concerned only with the commands in the chair project. Any framework commands won't be a part of this consolidation.


# chair CLI Commands

Under Click's structure, `chair` is the main command group, under which there are three main groups of commands in chair currently, namely

 - **install**: The install command group deals with commands used to install system dependencies for setting up VMRaid environment

 - **setup**: This command group for consists of commands used to maipulate the requirements and environments required by your VMRaid environment

 - **config**: The config command group deals with making changes in the current chair (not the CLI tool) configuration


## Using the chair command line

```zsh
➜ chair
Usage: chair [OPTIONS] COMMAND [ARGS]...

  Chair manager for VMRaid

Options:
  --version
  --help     Show this message and exit.

Commands:
  backup                   Backup single site
  backup-all-sites         Backup all sites in current chair
  config                   Change chair configuration
  disable-production       Disables production environment for the chair.
  download-translations    Download latest translations
  exclude-app              Exclude app from updating
  find                     Finds chaires recursively from location
  get-app                  Clone an app from the internet or filesystem and...
```

Similarly, all available flags and options can be checked for commands individually by executing them with the `--help` flag. The `init` command for instance:

```zsh
➜ chair init --help
Usage: chair init [OPTIONS] PATH

  Initialize a new chair instance in the specified path

Options:
  --python TEXT                   Path to Python Executable.
  --ignore-exist                  Ignore if Chair instance exists.
  --apps_path TEXT                path to json files with apps to install
                                  after init
```



## chair and sudo

Some chair commands may require sudo, such as some `setup` commands and everything else under the `install` commands group. For these commands, you may not be asked for your root password if sudoers setup has been done. The security implications, well we'll talk about those soon.



## General Commands

These commands belong directly to the chair group so they can be invoked directly prefixing each with `chair` in your shell. Therefore, the usage for these commands is as

```zsh
    chair COMMAND [ARGS]...
```

### The usual commands

 - **init**: Initialize a new chair instance in the specified path. This sets up a complete chair folder with an `apps` folder which contains all the VMRaid apps available in the current chair, `sites` folder that stores all site data seperated by individual site folders, `config` folder that contains your redis, NGINX and supervisor configuration files. The `env` folder consists of all python dependencies the current chair and installed VMRaid applications have.
 - **restart**: Restart web, supervisor, systemd processes units. Used in production setup.
 - **update**: If executed in a chair directory, without any flags will backup, pull, setup requirements, build, run patches and restart chair. Using specific flags will only do certain tasks instead of all.
 - **migrate-env**: Migrate Virtual Environment to desired Python version. This regenerates the `env` folder with the specified Python version.
 - **retry-upgrade**: Retry a failed upgrade
 - **disable-production**: Disables production environment for the chair.
 - **renew-lets-encrypt**: Renew Let's Encrypt certificate for site SSL.
 - **backup**: Backup single site data. Can be used to backup files as well.
 - **backup-all-sites**: Backup all sites in current chair.

 - **get-app**: Download an app from the internet or filesystem and set it up in your chair. This clones the git repo of the VMRaid project and installs it in the chair environment.
 - **remove-app**: Completely remove app from chair and re-build assets if not installed on any site.
 - **exclude-app**: Exclude app from updating during a `chair update`
 - **include-app**: Include app for updating. All VMRaid applications are included by default when installed.
 - **remote-set-url**: Set app remote url
 - **remote-reset-url**: Reset app remote url to vmraid official
 - **remote-urls**: Show apps remote url
 - **switch-to-branch**: Switch all apps to specified branch, or specify apps separated by space
 - **switch-to-develop**: Switch VMRaid and ERPAdda to develop branch


### A little advanced

 - **set-nginx-port**: Set NGINX port for site
 - **set-ssl-certificate**: Set SSL certificate path for site
 - **set-ssl-key**: Set SSL certificate private key path for site
 - **set-url-root**: Set URL root for site
 - **set-mariadb-host**: Set MariaDB host for chair
 - **set-redis-cache-host**: Set Redis cache host for chair
 - **set-redis-queue-host**: Set Redis queue host for chair
 - **set-redis-socketio-host**: Set Redis socketio host for chair
 - **use**: Set default site for chair
 - **download-translations**: Download latest translations


### Developer's commands

 - **start**: Start VMRaid development processes. Uses the Procfile to start the VMRaid development environment.
 - **src**: Prints chair source folder path, which can be used to cd into the chair installation repository by `cd $(chair src)`.
 - **find**: Finds chaires recursively from location or specified path.
 - **pip**: Use the current chair's pip to manage Python packages. For help about pip usage: `chair pip help [COMMAND]` or `chair pip [COMMAND] -h`.
 - **new-app**: Create a new VMRaid application under apps folder.


### Release chair
 - **release**: Create a release of a VMRaid application
 - **prepare-beta-release**: Prepare major beta release from develop branch



## Setup commands

The setup commands used for setting up the VMRaid environment in context of the current chair need to be executed using `chair setup` as the prefix. So, the general usage of these commands is as

```zsh
    chair setup COMMAND [ARGS]...
```

 - **sudoers**: Add commands to sudoers list for allowing chair commands execution without root password

 - **env**: Setup virtualenv for chair. This sets up a `env` folder under the root of the chair directory.
 - **redis**: Generates configuration for Redis
 - **fonts**: Add VMRaid fonts to system
 - **config**: Generate or over-write sites/common_site_config.json
 - **backups**: Add cronjob for chair backups
 - **socketio**: Setup node dependencies for socketio server
 - **requirements**: Setup Python and Node dependencies

 - **manager**: Setup `chair-manager.local` site with the [Chair Manager](https://github.com/vmraid/chair_manager) app, a GUI for chair installed on it.

 - **procfile**: Generate Procfile for chair start

 - **production**: Setup VMRaid production environment for specific user. This installs ansible, NGINX, supervisor, fail2ban and generates the respective configuration files.
 - **nginx**: Generate configuration files for NGINX
 - **fail2ban**: Setup fail2ban, an intrusion prevention software framework that protects computer servers from brute-force attacks
 - **systemd**: Generate configuration for systemd
 - **firewall**: Setup firewall for system
 - **ssh-port**: Set SSH Port for system
 - **reload-nginx**: Checks NGINX config file and reloads service
 - **supervisor**: Generate configuration for supervisor
 - **lets-encrypt**: Setup lets-encrypt SSL for site
 - **wildcard-ssl**: Setup wildcard SSL certificate for multi-tenant chair

 - **add-domain**: Add a custom domain to a particular site
 - **remove-domain**: Remove custom domain from a site
 - **sync-domains**: Check if there is a change in domains. If yes, updates the domains list.

 - **role**: Install dependencies via ansible roles



## Config commands

The config group commands are used for manipulating configurations in the current chair context. The usage for these commands is as

```zsh
    chair config COMMAND [ARGS]...
```

 - **set-common-config**: Set value in common config
 - **remove-common-config**: Remove specific keys from current chair's common config

 - **update_chair_on_update**: Enable/Disable chair updates on running chair update
 - **restart_supervisor_on_update**: Enable/Disable auto restart of supervisor processes
 - **restart_systemd_on_update**: Enable/Disable auto restart of systemd units
 - **dns_multitenant**: Enable/Disable chair multitenancy on running chair update
 - **serve_default_site**: Configure nginx to serve the default site on port 80
 - **http_timeout**: Set HTTP timeout



## Install commands

The install group commands are used for manipulating system level dependencies. The usage for these commands is as

```zsh
    chair install COMMAND [ARGS]...
```

 - **prerequisites**: Installs pre-requisite libraries, essential tools like b2zip, htop, screen, vim, x11-fonts, python libs, cups and Redis
 - **nodejs**: Installs Node.js v8
 - **nginx**: Installs NGINX. If user is specified, sudoers is setup for that user
 - **packer**: Installs Oracle virtualbox and packer 1.2.1
 - **psutil**: Installs psutil via pip
 - **mariadb**: Install and setup MariaDB of specified version and root password
 - **wkhtmltopdf**: Installs wkhtmltopdf v0.12.3 for linux
 - **supervisor**: Installs supervisor. If user is specified, sudoers is setup for that user
 - **fail2ban**: Install fail2ban, an intrusion prevention software framework that protects computer servers from brute-force attacks
 - **virtualbox**: Installs supervisor
