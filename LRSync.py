# Lightroom sync utility
# usage: LRSync <catalogpath> <savedir> [-showonly]
# where <catalogpath> is the full path to the local Lightroom catalog (.lrcat)
#       <savedir> is the backup folder containing subfolders with .zip backups
#       -showonly: if present, do not copy but show action only

import sys
import os
import glob
import datetime
import zipfile

catalogpath = sys.argv[1]
savedir = sys.argv[2]
showonly = False
if ((len(sys.argv) > 3) and (sys.argv[3] == "-showonly")):
    showonly = True

#print("Catalog: " + catalogpath + " Backup folder: " + savedir + " -showonly=" + str(showonly))

# get modified time of local catalog
catalog_exists = os.path.isfile(catalogpath)
#print("catalog_exists = " + catalog_exists)
if catalog_exists:
    catalog_time = os.path.getmtime(catalogpath)
    print("Catalog: " + catalogpath + " " + datetime.datetime.fromtimestamp(catalog_time).strftime("%c"))
else:
    catalog_time = datetime.MINYEAR
    print("Catalog: " + catalogpath + " does not exist.")

# find newest backups
search = savedir + "/**/*.zip"
newest = datetime.MINYEAR
newest_file = ""
print("Searching: " + search)
for zip in glob.iglob(search, recursive=True):
    filetime = os.path.getmtime(zip)
    if filetime > newest:
        newest = filetime
        newest_file = zip
#    print(zipfile + "Modified: " + filetime.strftime("%c"))

if newest_file == "":
    print("No .zip backup files found, exiting...")
    exit(0)

if catalog_exists and catalog_time >= newest:
    print("Local catalog is up to date, exiting...")
    exit(0)

print("Restoring backup: " + newest_file + " " + datetime.datetime.fromtimestamp(filetime).strftime("%c"))

zipfile_to_restore = zipfile.ZipFile(newest_file)
found = False
catalog_file = os.path.basename(catalogpath)
for saved_catalog in zipfile_to_restore.namelist():
    if (saved_catalog == catalog_file):
        found = True
        break

if not found:
    print("Catalog file not found.")
    exit(1)

# copy backed up catalog, overwriting old...
if (showonly):
    exit(0)

print("Extracting...")
#restore_path = "/Users/john"
restore_path = os.path.dirname(catalogpath)
print("Restoring: " + catalog_file + " to: " + restore_path)
zipfile_to_restore.extract(catalog_file, restore_path)
