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
import re
import json
from argparse import ArgumentParser

verbose_output = False


def message(message):
    if verbose_output:
        print(message)


def update_catalog(catalogpath, backupfolder, showonly=False):
    # get modified time of local catalog
    catalog_time = datetime.datetime.fromtimestamp(os.path.getmtime(catalogpath))

    # find newest backups
    search = backupfolder + "/**/*.zip"
    """def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]"""

    catalog_filename = os.path.split(catalogpath)[1]
    backup_subfolders = [d for d in os.listdir(backupfolder) if os.path.isdir(os.path.join(backupfolder, d))]
    newest = None
    newest_backup_file = None
    for d in backup_subfolders:
        groups = re.match(r'(\d{4})-(\d{2})-(\d{2}) (\d{2})(\d{2})', d)
        if groups:
            backup_path = os.path.join(backupfolder, d, catalog_filename + '.zip')
            if not os.path.exists(backup_path):
                continue
            year = int(groups[1])
            month = int(groups[2])
            day = int(groups[3])
            hour = int(groups[4])
            minute = int(groups[5])
            ts = datetime.datetime(year, month, day, hour, minute)
            if newest is None or ts > newest:
                newest = ts
                newest_backup_file = backup_path

    if newest_backup_file is None:
        message(f'No .zip backup files found for {catalogpath}.')
        return True

    if catalog_time >= newest:
        message(f'Local catalog "{catalogpath}" is newer than "{newest_backup_file}", no update.')
        return True

    message(f'Restoring backup:{newest_backup_file} ({newest})')

    zipfile_to_restore = zipfile.ZipFile(newest_backup_file)
    found = False
    catalog_file = os.path.basename(catalogpath)
    for saved_catalog in zipfile_to_restore.namelist():
        if (saved_catalog == catalog_file):
            found = True
            break

    if not found:
        message('Catalog file not found.')
        exit(1)

    message("Extracting...")
    restore_path = os.path.dirname(catalogpath)
    message(f'Restoring: "{catalog_file}" to "{restore_path}"')
    if showonly:
        message('--showonly: skipping actual copy')
        return True
    zipfile_to_restore.extract(catalog_file, restore_path)
    return True


def get_folders(system_name, folders):
    CATALOG = 'catalog_folder'
    BACKUP = 'backup_folder'
    catalogfolder = folders[0]
    backupfolder = folders[1]
    json_filename = 'LRSync.json'
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as f:
            info = json.load(f)
    else:
        info = dict()

    if system_name in info:
        if catalogfolder is None:
            catalogfolder = info[system_name][CATALOG]
        else:
            message(f'Saving catalogfolder="{catalogfolder}" for "{system_name}" to configuration file.')
            info[system_name][CATALOG] = catalogfolder
        if backupfolder is None:
            backupfolder = info[system_name][BACKUP]
        else:
            message(f'Saving backupfolder="{backupfolder}" for "{system_name}" to configuration file.')
            info[system_name][BACKUP] = backupfolder
    else:
        if catalogfolder is None or backupfolder is None:
            return False
        message(f'Creating folder information for "{system_name}" : catalogfolder="{catalogfolder}" backupfolder="{backupfolder}"')
        info[system_name] = {CATALOG: catalogfolder,
                             BACKUP: backupfolder}

    with open(json_filename, 'w') as f:
        json.dump(info, f, indent=4)

    folders[0] = catalogfolder
    folders[1] = backupfolder
    return True


def update_catalogs(catalogfolder, backupfolder, showonly=False):
    # get catalog filenames
    catalog_filenames = glob.glob(catalogfolder + '/*.lrcat')
    for catalog in catalog_filenames:
        update_catalog(catalog, backupfolder, showonly)


if __name__ == '__main__':
    system_name = os.uname()[1]
    parser = ArgumentParser()
    parser.add_argument('--catalogfolder', help='Folder where local Lightroom catalogs maintained', required=False)
    parser.add_argument('--backupfolder', help='Folder containing catalog backups', required=False)
    parser.add_argument('--showonly', help='Take no action, only show operations that would be performed',
                        action='store_true')
    parser.add_argument('--verbose', help='Verbose output', action='store_true', required=False, default=False)
    args = parser.parse_args()
    verbose_output = args.verbose
    folders = [args.catalogfolder, args.backupfolder]
    if not get_folders(system_name, folders):
        print(f'--catalogfoler and/or --backupfolder not given and no existing info for "{system_name}" in configuration')
        sys.exit(1)

    result = update_catalogs(folders[0], folders[1], args.showonly)
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
