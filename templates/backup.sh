#/bin/bash
# Site: {site}
# Home: {site_home}
# Backup to: {backup_dir}

timestamp=$(date '+%y%m%d-%H%M%S')
cd {site_home}
tar -zcf {backup_dir}/$timestamp-{site}.tgz *
