#/bin/bash

# Backup timestamp
timestamp=$(date '+%y%m%d-%H%M%S')

cd {site_home}
tar -zcf {backup_dir}/$timestamp-{site}.tgz *
