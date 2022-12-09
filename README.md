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

## Userscript

### PrebooruFileUpload

A userscript for uploading illusts with dead sources to danbooru.

- **Page:** https://gist.github.com/BrokenEagle/35f46ecfb4f9c13bc97efc968bcf396e
- **Download:** https://gist.github.com/BrokenEagle/35f46ecfb4f9c13bc97efc968bcf396e/raw/PrebooruFileUpload.user.js

### NTISAS

A userscript which shows Tweets already uploaded to Danbooru as well as provides other additional functionality.

- **Info:** https://github.com/BrokenEagle/JavaScripts/wiki/Twitter-Image-Searches-and-Stuff
- **Forum page:** https://danbooru.donmai.us/forum_topics/16342

There is a branch of NTISAS under development which adds support for uploading and querying data from Prebooru.

- **Download:** https://raw.githubusercontent.com/BrokenEagle/JavaScripts/ntisas-prebooru/New_Twitter_Image_Searches_and_Stuff.user.js

### NPISAS

(Under development)

# To-Do

1. Add usage wikis.
2. Add tests for the code.
3. Pool reorder page.
4. Add order filters to searchable.
5. User tags for posts. (\*\*DONE\*\*)
6. Tag categories, and maybe illust/post count.
7. Generalized query parameter which would use query arguments parameterized by logical operators instead of being hamstrung by URL arguments.
8. Add automatic artist webpage URL unshortening.
9. Pool elements, similarity matches, similarity data INDEX page(s). (\*\*PARTIALLY DONE\*\*)
10. Drop unused columns or those used mostly for testing. (\*\*PARTIALLY DONE\*\*)
11. Server status page and ping functions.
12. Network upload link for unuploaded illust URLs.
13. Add series column and navigation to pools. (\*\*DONE\*\*)
14. Add full URL to illust URL JSON. (\*\*DONE\*\*)
15. Subscribe to artists. (\*\*DONE\*\*)
    - Mandatory recheck interval.
    - Optional expiration, with either hard deletion or archiving.
    - Posts created with subscriptions will be segregated from those created via user interaction.
16. Archive posts/illusts/artists/boorus. (\*\*DONE\*\*)
17. Add `parent_id` and `updated` column to posts.
   - To allow parent/child relationships.
18. On uploads select, have an asynchronous process download all of the images. (\*\*DONE\*\*)
    - Currently the user is forced to wait until all of the previews have been downloaded.
19. Have pagination for uploads/illusts, since some Pixiv artworks can have well over 10 images.
20. Add `banned` column to boorus which will match the artist's status on Danbooru. (\*\*DONE\*\*)
21. Backup/export/import the DB from the script itself.
22. Add delete method to more types.
    - Save JSON of data in a separate table when this is done to allow for delete operations to be undone.
    - Have a configuratble expiration time for when the data will be purged, to include immediate or never.
23. Add support for Pixiv ugoiras.
24. Use video container for MP4 videos and run them in a loop.
25. Add helper script to generate NTISAS/NPISAS import files to quickly populate the data.
26. Add include and only parameters for json endpoints.
    - Includes will chain include relationship models.
    - Only will limit the values returned.
27. Connect multiple Preboorus together as an Overbooru.
28. Sequential pagination
    - i.e. Danbooru style with 'a' or 'b' prefixes.
29. Other selection mechanics, such as drag-select.

*And much, much, more...*
