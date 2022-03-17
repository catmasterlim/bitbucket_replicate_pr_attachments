## Disclaimer
This tool was NOT written by Atlassian developers and is considered a third-party tool. This means that this is also NOT supported by Atlassian. We highly recommend you have your team review the script before running it to ensure you understand the steps and actions taking place, as Atlassian is not responsible for the resulting configuration.

## Purpose
This script was intended to scan a server/dc instance, locating all attachments within a given pull request, and then download/upload it into the matching repo/pr within Bitbucket Cloud as the BCMA plugin does not perform this action. This script is mostly complete but i ran into an issue with uploading the actual downloaded items to Bitbucket Cloud as you can't attach anything outside of image files into a PR, and doing so doesn't have a normal API.

It may be possible to still upload the images via the normal api endpoint (below) but looking at the network tab of a browser's "developer panel" we see that it actually makes a call against a "/xhr/..." URI which may not be something we can interact with via the API. Even still, it referrences a regex "r[\w+]" string which represents the repo id on the backend which we do not have a way of knowing in advance. It may be possible but requires more investigation.

api endpoint to create comment in a PR (and theoretically upload an attachment/image)
https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-pull-request-id-comments-get


## How to Use
Edit rename/copy the "env-template.py" file to "env.py" (as env.py is in the .gitignore) and fill it out accordingly.

Configure a python virtual environment and install package dependencies with the follow commands:

        python3 -m venv venv
        source venv/Scripts/activate  # If using gitbash on Windows
        source venv/bin/activate      # If on linux/mac
        pip3 install -r requirements.txt

Run script with python via:

        python3 bitbucket_api.py

Note:
This script was written in python 3.8
