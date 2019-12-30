# LightRoom catalog check
# This program examines the timestamp of catalogs on the local hard drive and compares to the timestamps of
# catalogs saved in backup .ZIP files on an external drive.

import argparse
import glob
import os
import datetime
import zipfile


def get_local_catalogs(folder, catalog_ext='.lrcat'):
    files = [f for f in os.listdir(folder) if f.endswith(catalog_ext)]
    return files

def get_latest_zip_backup(folder, catalog_name):
    search = f'{folder}/**/{catalog_name}.zip'
    newest = datetime.MINYEAR
    newest_file = None
    for zip in glob.iglob(search, recursive=True):
        filetime = os.path.getmtime(zip)
        if filetime > newest:
            newest = filetime
            newest_file = zip
    return newest_file


def restore_catalog(zip_filename, catalog_filename, folder, showonly=False):
    if showonly:
        print(f'Restoring {catalog_filename} from {zip_filename} to folder {folder}')
    else:
        zipfile_to_restore = zipfile.ZipFile(zip_filename)
        zipfile_to_restore.extract(catalog_filename, folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Synchronize Lightroom catalogs')
    parser.add_argument('--catalogs', help='Folder where local Lightroom catalogs are stored', required=True)
    parser.add_argument('--backups', help='Folder with backups of catalogs from other system', required=True)
    parser.add_argument('--catext', help='Catalog file extension', default='.lrcat')
    parser.add_argument('--showonly', help='Show files that would be copied', action='store_true', default=False)

    args = parser.parse_args()

    catalog_files = get_local_catalogs(args.catalogs, catalog_ext=args.catext)

    for catalog in catalog_files:
        backup_catalog = get_latest_zip_backup(args.backups, catalog)
        if backup_catalog is not None:
            backup_time = os.path.getmtime(backup_catalog)
            catalog_fullpath = os.path.join(args.catalogs, catalog)
            catalog_time = os.path.getmtime(catalog_fullpath)
            if backup_time > catalog_time:
                restore_catalog(backup_catalog, catalog, args.catalogs, args.showonly)

    print('Done.')
