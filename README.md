# gphotos-uploader

Upload directories of files to [Google Photos](https://www.google.com/photos/about/) albums.

#### Overview
* :notebook: Uploads can only be sent to albums created by the same application (see "Create Album" below)
* :floppy_disk: Records are kept when an upload is completed so that files are not sent multiple times, but the Google Photos API appears to prevent duplicates in the same album well
* :closed_lock_with_key: Authentication and authorization are done via OAuth, you will need to register an application in Google Cloud and then grant it access to your photo library (see "Setup" below)
* :no_entry_sign: Files are not deleted from Google Photos album when removed locally

## Setup

#### Create Application

1. Follow the steps [here](https://developers.google.com/photos/library/guides/get-started) to create a new [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2) application **and** enable the [Google Photos API](https://developers.google.com/photos/library/reference/rest).
2. Follow steps **1-4** [here](https://developers.google.com/photos/library/guides/get-started#request-id) to generate application credentials.
	* Set application type to "Desktop"
3. Select the credentials created from the previous step and click on "DOWNLOAD JSON"
4. Setup credentials file to default location (can override with CLI params)
	* Move the downloaded file to the root of this project
	* Re-name file to `credentials.json`


#### Install Requirements

Create virtual env and install requirements.
```
$ python -m venv env
$ source env/bin/activate
$ (env) pip install -r requirements.txt
```

#### Authorize User for Application

:warning: This process requires a web browser.

:bulb: After generating a user token, you can move it to a headless machine.

1. Run the CLI tool, a browser may automatically open and a URL will be printed to the console.
```
$ (env) python cly.py create-auth
```

2. Following the URL in the previous step, authorized the application to manage your user's photo library.
	* You will likely see a warning the application has not been reviewed by Google
3. Verify a user token file is created at `auth_token.json` in the root of this project (or elsewhere if you overrode the CLI params)


## Usage

```
usage: cli.py [-h] [--app-data APP_DATA] {create-auth,list-albums,create-album,upload-album} ...

positional arguments:
  {create-auth,list-albums,create-album,upload-album}
    create-auth         retrieve valid auth token
    list-albums         list locally registred albums, and optionally all remote ones
    create-album        make new album in cloud and register locally
    upload-album        upload new content from local dir to cloud album

optional arguments:
  -h, --help            show this help message and exit
  --app-data APP_DATA   filename to store app data in sqlite (default: <project_dir>/database/.app_data)
```

### Create Album

Creates a new album on Google Photos **and** registers it locally in the app database.

```
usage: cli.py create-album [-h] [--token-file TOKEN_FILE] name

positional arguments:
  name                  name for new album

optional arguments:
  -h, --help            show this help message and exit
  --token-file TOKEN_FILE
                        filename for oauth user token (default: <project_dir>/auth_token.json)
```

### List Albums

List all locally registered by application in the app database, optinally showing remote ones as well.

:bulb: The integer `id` column is used for the `upload-album` command, the `gid` column is the identifier of the album on Google Photos and is used to make API calls.

```
usage: cli.py list-albums [-h]

optional arguments:
  -h, --help  show this help message and exit
  -a                    include remote albums (default: False)
  --token-file TOKEN_FILE
                        filename for oauth user token, only relevent if -a is set (default: <project_dir>/auth_token.json)
```

### Upload Album

:warning: Uploads can only be performed by the same application which created the album! This is a requirement of the API, not this tool.

:bulb: Uploads are recorded in the database and not repeated when running again.

```
usage: cli.py upload-album [-h] [--token-file TOKEN_FILE] [-e] from_dir to_album

positional arguments:
  from_dir              local folder to upload to gphotos
  to_album              id of albumn in db to upload into

optional arguments:
  -h, --help            show this help message and exit
  --token-file TOKEN_FILE
                        filename for oauth user token (default: <project_dir>/auth_token.json)
  -e                    exit non-zero if any uploads in batch failed (default: False)
```
