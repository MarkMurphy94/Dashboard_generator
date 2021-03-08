# ADS Dashboard Tool
This webapp is designed to create standardized test plans and dashboards for GTO projects.

## Before you deploy...

- Generate a Personal Access Token.
  - Do this if you have write access to all test plans and queries. Otherwise get a copy from Mark Murphy or Jorge Rincon
  - Click User Settings > Personal access tokens in the top-right menu in ADS. Then click "+New Token". Save your token somewhere safe.
- Determine the IP address the tool will be hosted on.
  - In the instructions below, this address is referred to by **`<HOST_ADDRESS>`**
- Determine the port you will be using.
  - In the instructions below, this port is referred to by **`<PORT>`**
  - If no port is specified, the tool will run on port :8000.
- Git Reminders!
  - Each time you perform a git command, you will be prompted for 'itron@dev.azure.com' credentials. Generate these in the Clone menu by clicking "Generate Git Credentials".
  - It may be handy to keep this password in your clipboard until you're finished with the deploy. Or use `git config credentials.helper store` to store your credentials.

---

# Deploying to a Linux environment for the first time

In the installation directory:
- Initial checks:
  - Make sure python 3.6 or greater is installed.
  - If you're using a virtual environment, you may need to install it again as python3.
```
$ python --version
$ pip install virtualenv            # any virtual environment should work, but we'll use virtualenv.
                                    # !! IF YOU USE A DIFFERENT ENVIRONMENT HANDLER, ADD THE ENV FOLDER TO .gitignore!!
```
- Obtain the code with `git clone`, then enter the directory.
```
$ git clone https://itron@dev.azure.com/itron/SoftwareProducts/_git/ADS_DASH_TOOL
$ cd ADS_DASH_TOOL
```
- In the `settings.py` file, add **`<HOST_ADDRESS>`** to the `ALLOWED_HOSTS` array.
```
$ vim ads_site/ads_site/settings.py
```
- Copy your personal access token to `ads_site/ads_app/static/token.txt`.
```
$ vim ads_site/ads_app/static/token.txt
```
- (Optional) Setup your virtual environment. In our example, virtualenv creates a folder named `venv`.
- (Optional) Activate your virtual environment and install the required packages using `ADS_DASH_TOOL/requirements.txt`
```
$ virtualenv venv                   # NOTE: you may have to specify the python version with '--python=python3'
$ source venv/bin/activate          # This command activates the virtual environment
(venv)$ pip install -r requirements.txt
```
- **If you have an existing sqlite3 user database, copy it to `ADS_DASH_TOOL/ads_site/db.sqlite3`!**
- Run the server at **`<HOST_ADDRESS>:<PORT>`** from the folder `ADS_DASH_TOOL/ads_site`.
  - The `nohup ... &` command will leave the server running in the background. You can safely exit the shell if you start it this way.
```
(venv)$ cd ads_site
(venv)$ python manage.py migrate    # This command updates the database schema. This may not be required if you are using an existing database.
(venv)$ nohup python manage.py runserver <HOST ADDRESS>:<PORT> &
```

## After this deploy

All server output will be written to `ADS_DASH_TOOL/ads_site/nohup.out`. User activity will be written to `ADS_DASH_TOOL/ads_site/ads_app/logs.txt`.
You can monitor the server with `tail`.
```
$ tail -f nohup.out
$ tail -f ads_app/logs.txt
``` 

---

# Hot patching the ADS Dashboard Tool

You can quickly deploy a new version of the tool by simply pulling in the changes from the repo.
- You can deploy this way **only if**:
  - You do not need to archive the logs
  - You are certain that the existing config files and database will not conflict with the patch
  - You have already notified users that there will be a brief interruption of service at patch time.
```
$ git fetch --all
$ git stash               # stash is needed to preserve your settings.py configurations
$ git checkout <PATCH_BRANCH>
$ git stash pop           # stash pop restores your settings.py configurations on the new branch
```

The Django framework will catch the changes and restart the server automatically. **This may interrupt users if they are creating ADS items!**

---

# Updating an existing instance of the ADS Dashboard Tool

In the installation directory:
- Navigate to the git folder and fetch the latest versions
```
$ cd ADS_DASH_TOOL
$ git fetch --all --tags
```
- Shut down the server.
  - There will be two or more processes with the correct `<PORT>`. Kill the process which lists the full python executable.
```
$ ps -aux | grep {'runserver' OR '<PORT>'}
$ kill -2 <pid>
```
- Backup the database and archive the nohup.out. Stash your `settings.py` file if you need to retain that configuration.
  - Check the `ADS_DASH_TOOL/ads_site/logs` folder for any existing logs. If any exist, be sure to archive the new logs with an incremented filename.
  - (ex: `logs/` contains `nohup.old.1` and `nohup.old.2`. Save the new file as `nohup.old.3`)
```
$ cp ads_site/db.sqlite3 ~/backup.sqlite3
$ (OPTIONAL) mkdir ads_site/logs
$ ls ads_site/logs/
$ cp ads_site/nohup.out ads_site/logs/nohup.old.#
$ (OPTIONAL) git stash
```
- Checkout the latest version (v#.#) and run the server
```
$ git checkout v#.#
$ (OPTIONAL) git stash pop                          # restore your settings.py configuration if you stashed it earlier
$ source venv/bin/activate
(venv)$ pip install -r requirements.txt
(venv)$ vim ads_site/ads_site/settings.py           # add '<HOST_ADDRESS>' to ALLOWED_HOSTS array if you did not stash the configuration
(venv)$ python manage.py migrate
(venv)$ nohup python manage.py runserver <HOST_ADDRESS>:<PORT> &
```