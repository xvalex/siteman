#!/usr/bin/env python
import argparse, sys, os, shutil
import config

def remove_if_exists(f):
    if os.path.lexists(f):
        os.remove(f)

def rmtree_if_exists(f):
    if os.path.lexists(f):
        shutil.rmtree(f)

###############################################################################
# Parse arguments

parser = argparse.ArgumentParser(description = 'Delete site [and user] data.')

parser.add_argument('--site', type=str, nargs=1, required=True,
                    help='Site domain')

parser.add_argument('--user', type=str, nargs=1, required=True,
                    help='User owns this site')

parser.add_argument('--wwwuser', type=str, nargs=1, default=[ config.default_wwwuser ],
                    help="www user (default: '" + config.default_wwwuser + "'")

parser.add_argument('--wwwgroup', type=str, nargs=1, default=[ config.default_wwwgroup ],
                    help="www group (default: '" + config.default_wwwgroup + "'")

parser.add_argument('--phpver', type=str, nargs=1, default=[ config.default_phpver ],
                    help="PHP Version (default: '" + config.default_phpver + "'")

parser.add_argument('--remove-user', action='store_true',
                    help='Create new user for this site')

args = parser.parse_args()

###############################################################################

site = args.site[0]
user = args.user[0]
group = args.user[0]
wwwuser = args.wwwuser[0]
wwwgroup = args.wwwgroup[0]
phpver = args.phpver[0]

keys = {
    'site': site,
    'user': user,
    'group': group,
    'wwwuser': wwwuser,
    'wwwgroup': wwwgroup,
    'phpver': phpver
}

site_home = config.site_home.format(**keys)
user_home = config.user_home.format(**keys)
backup_dir = config.backup_dir.format(**keys)
phppool_conf = config.phppool_conf.format(**keys)
nginx_conf = config.nginx_conf.format(**keys)
create_user_cmd = config.create_user_cmd.format(**keys)
delete_user_cmd = config.delete_user_cmd.format(**keys)
reload_cmd = config.reload_cmd.format(**keys)

###############################################################################
# Remove config files

print("Removing '" + nginx_conf + "'")
remove_if_exists(nginx_conf)

print("Removing '" + phppool_conf + "'")
remove_if_exists(phppool_conf)

###############################################################################
# Reload services

print "Reloading services"
os.system(reload_cmd)

###############################################################################
# Clean user home or remove user

if args.remove_user:
    print("Removing user '" + user + "' and its home")
    delete_user_cmd = delete_user_cmd
    os.system(delete_user_cmd)
else:
    path = os.path.join(user_home, site);
    print("Removing symlink '" + path + "'")
    remove_if_exists(path);

###############################################################################
# Remove site home

print("Removing site home '" + site_home + "'")
rmtree_if_exists(site_home + '/')
