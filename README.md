# Prebooru

Repository for downloading and storing artist data and images prior to being uploaded to a booru or for personal use.

# Installation

1. Copy the Prebooru project locally.

    `git clone https://github.com/BrokenEagle/Prebooru.git`

2. Run the installation script from the root directory.

    `setup.bat`

    **Note:** This can be done in a virtual Python environment in order to keep this install from conflicting with other projects.

3. Setup the configuration.

    - A. Create a local config file.

      Using the `app\default_config.py` as a reference, create `app\local_config.py` with the configuration specific to the user and machine.

      **Note:** The`default_config.py` is tracked by Git, but if that is not a concern, then it can be modified directly instead.

    - B. Set environment variables.

        Configuration can also be set via environment variables. Refer to `app\config.py` for the list of configuration variables currently suppported.

4. Initialize the database.

    `prebooru.py init`

5. Start the server.

    `prebooru.py server`

6. Install FFMPEG binaries (optional)

    Go to https://www.gyan.dev/ffmpeg/builds/ and download `ffmpeg-git-essentials.7z`. Copy the `ffprobe.exe` to the root directory.

    This allows the downloader to verify the dimensions and streams of MP4 videos before saving them to disk.

7. Install updated SQlite version (optional)

    Got to https://www.sqlite.org/download.html and download the latest binary for your OS. Replace the sqlite3.dll file in the DLLs folder
    of the current Python installation. This is the **DLLs** folder under the directory of the `python.exe` executable.

# Supported sites

There are currently only a few sites supported for automatic uploading. The following lists these sites and their supported request URL.

- Pixiv / artwork
    - https://www.pixiv.net/artworks/1234
- Twitter / tweet
    - https://twitter.com/nothing/status/1234

# Bookmarklets

Prebooru has two landing pages which support uploading directly with a source URL. The bookmarklets will open new tabs to these pages when on one of the supported site pages.

**Note:** The following assume the default IP address and port from the local config file. Replace these values if they are different.

## All

Will upload all images from a site post.

```
javascript:window.open('http://127.0.0.1:5000/uploads/all?upload[request_url]='+encodeURIComponent(location.href),'_blank');false;
```

## Select

Will go to a page with all of the preview images from a site post displayed, allowing one to select which images to upload.

```
javascript:window.open('http://127.0.0.1:5000/uploads/select?upload[request_url]='+encodeURIComponent(location.href),'_blank');false;
```

# Database migrations

As the application gets developed, the database schema may get adjusted as needed. When this occurs, the databases will need to go through a migration.

1. Set the necessary environment variables

    `set FLASK_APP=prebooru`

    `set FLASK_ENV=development`

    Setting these allows one to use the `flask` command with the application, which is how the database commands are accessed.

2. Check the current migration status

    `flask db current`

    There will be a hexadecimal number displayed for all of the databases. If there is not a `(head)` next to this number, then that means that the databases are not current.

3. Upgrade the databases

    `flask db upgrade`

    After this command executes, running `flask db current` again should show it at the latest version with `(head)` next to the number.

# Batch files

### `databasesave.bat`

An example batch file is present under the **misc\\** folder for backing up the contents of the database directory (as determined by the Prebooru config file) to an external drive.

### `initialize.bat`

A batch file for quickly setting the environment variables necessary to use the `flask` command from the command line. By default it sets the environment to `production`. To set the environment to `development` call the batch file with the argument `development`.

# External resources

## Image server

The default image server provided is functional, but isn't optimized at sending a lot of images at once. An alternate image server can be used instead for this purpose. If this is being done, then add the necessary information to the config file, as well as setting the following value.

```python
HAS_EXTERNAL_IMAGE_SERVER = True
```

### NGINX

- **Info:** http://nginx.org/en/docs/windows.html
- **Downlad:** http://nginx.org/en/download.html

An example configuration file (`nginx.conf`) is present under the **misc\\** folder. The **listen** line contains the port number, and by default it binds to **0.0.0.0**, so it will listen on all network adapters. The **root** line is the base directory where the images will reside (as determined by the Prebooru config file), and the filepath needs to use Linux-style directory separators "/" instead of Windows-style "\\".

Additionally, there is also a `nginx.bat` batch file there which can be modified as necessary as an aid to quickly starting or stopping this service.
