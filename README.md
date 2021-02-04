## ADS Dashboard Tool
This webapp is designed to create standardized test plans and dashboards for GTO projects.

## Before you deploy...

- Generate a Personal Access Token.
  - Do this if you have write access to all test plans and queries. Otherwise get a copy from Mark Murphy or Jorge Rincon
  - Click User Settings > Personal access tokens in the top-right menu in ADS. Then click "+New Token". Save your token somewhere safe.
- Determine the IP address the tool will be hosted on.
  - In the instructions below, this address is referred to by <HOST_ADDRESS>
- Determine the port you will be using.
  - In the instructions below, this port is referred to by <PORT>
  - If no port is specified, the tool will run on port :8000.
- Git Reminders!
  - Each time you perform a git command, you will be prompted for 'itron@dev.azure.com' credentials. Generate these in the Clone menu by clicking "Generate Git Credentials".
  - It may be handy to keep this password in your clipboard until you're finished with the deploy.

---

## Deploying the ADS Dashboard Tool for the first time

In the installation directory:
- Initial checks:
```
$ python --version                  # ensure python 3.6 or greater is installed here. You may also use a virtual environment instead.)
$ pip install virtualenv            # any virtual environment which allows you to use `pip install` should work.
```
- Obtain the code:
```
$ git clone https://itron@dev.azure.com/itron/SoftwareProducts/_git/ADS_DASH_TOOL
$ cd ADS_DASH_TOOL
$ vim ads_site/ads_site/settings.py        # add '<HOST_ADDRESS>' to ALLOWED_HOSTS array
$ vim ads_site/ads_app/static/token.txt    # copy your personal access token here
```
- Setup your virtual environment:
```
$ virtualenv venv                   # create venv folder to hold virtualenv configs
                                    # NOTE: you may have to specify the python version with '-p python3.6' for example
                                    # NOTE: if using a different virtual environment tool, add the env folder to .gitignore
$ source venv/bin/activate          # activate your virtual environment
(venv)$ pip install -r requirements.txt
```
- **If you have an existing sqlite3 user database, move it to `ads_site/db.sqlite3`**
- Run the server at <HOST_ADDRESS>:<PORT>
```
(venv)$ cd ads_site                 # this is the folder that contains manage.py
(venv)$ python manage.py migrate    # update the database schema. This may not be required if you are using an existing database.
(venv)$ nohup python manage.py runserver <HOST ADDRESS>:<PORT> &   # run server in the background. all output is written to nohup.out
```

---

## Updating an existing instance of the ADS Dashboard Tool

In the installation directory:
- Navigate to the git folder and fetch the latest versions
```
$ cd ADS_DASH_TOOL
$ git fetch --all --tags
```
- Shut down the server
```
$ ps -aux | grep {'runserver' OR <PORT>}    # find the pid of the current server ON THE CORRECT PORT
$ kill -2 <pid>                             # kill process using the pid found above using SIGINT (SIGINT = Ctrl+C)
                                            # repeat this process 2 or 3 times until there are no more server processes running on the port.
```
- Archive the nohup.out
```
$ cp ads_site/db.sqlite3 ~/backup.sqlite3     # back up the database in case it is overwritten
$ ls logs/                                  # see the current log archive
$ cp nohup.out logs/nohup.old.#             # copy logs to archive using incremented number #
```
- Checkout the latest version and run the server
```
$ git checkout v#.#                         # checkout the latest version
$ virtualenv venv                           # create venv folder to hold virtualenv configs
$ source venv/bin/activate
(venv)$ pip install -r requirements
(venv)$ vim ads_site/ads_site/settings.py            # add '<HOST_ADDRESS>' to ALLOWED_HOSTS array if it's not already there
(venv)$ python manage.py migrate
(venv)$ nohup python manage.py runserver <HOST_ADDRESS>:<PORT> &   # run server in the background. all output is written to nohup.out
```