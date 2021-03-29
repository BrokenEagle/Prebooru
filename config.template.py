# CONFIG.PY
"""Primary use is to store environment variables"""

#GLOBAL VARIABLES

###WINDOWS###
"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""
workingdirectory = "C:\\temp\\"
datafilepath = "data\\"
jsonfilepath = "json\\"
imagefilepath = "pictures\\"


###LINUX###
'''
"""Filepaths need to end with a forwardslash ('/')"""
workingdirectory = "/home/USERNAME/temp/"
datafilepath = "data/"
jsonfilepath = "json/"
imagefilepath = "pictures/"
'''

# The user ID of the system
SYSTEM_USER_ID = 2

# Log into Pixiv and get this value from the cookie PHPSESSID
PIXIV_PHPSESSID = ""
