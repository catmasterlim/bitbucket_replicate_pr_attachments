## Disclaimer
This tool was NOT written by Atlassian developers and is considered a third-party tool. This means that this is also NOT supported by Atlassian. We highly recommend you have your team review the script before running it to ensure you understand the steps and actions taking place, as Atlassian is not responsible for the resulting configuration.

## Purpose
This script is intended to scan a server/dc instance, locating all attachments within all pull requests, and then download/upload it into the matching repo/pr within Bitbucket Cloud as the BCMA plugin does not perform this action.

The process involves locating all attachments within comments by reading any particular PR's activity log. Once we identify the file, we can download it to the local working machine. We replace space characters with underscores, since that will happen anyway when uploading to cloud but we do it early to better keep track of everything, and then we append the PR id (of the PR it belongs to) as well as a random 8 digit hash to the end of the filename (before the file's extension) to make sure it's unique and won't collide with any other files that we previously uploaded. Once the file exists in the new repo's "downloads" folder, we can then hyperlink to it from a new pr comment in the matching prs.

## How to Use
Edit rename/copy the "env-template.py" file to "env.py" (as env.py is in the .gitignore) and fill it out accordingly.

Configure a python virtual environment and install package dependencies with the follow commands:

        python3 -m venv venv
        source venv/Scripts/activate  # If using gitbash on Windows
        source venv/bin/activate      # If on linux/mac
        pip3 install -r requirements.txt

Set username/password details

        cp env-template.py env.py
        # Open the new env.py and fill in the blanks as per the comments and save the file

Run the script with python via:

        python3 bitbucket_api.py

Note:
This script was written in python 3.10
