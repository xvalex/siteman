#!/usr/bin/env python
import argparse, sys, os, shutil
from config import *

def remove_if_exists(f):
    if os.path.lexists(f):
        os.remove(f)

def rmtree_if_exists(f):
    if os.path.lexists(f):
        shutil.rmtree(f)

parser = argparse.ArgumentParser(description = 'Delete site [and user] data.')

parser.add_argument('--site', type=str, nargs=1, required=True,
                    help='Site domain')

parser.add_argument('--user', type=str, nargs=1, required=True,
                    help='User owns this site')

parser.add_argument("--remove-user", action="store_true",
                    help="Remove user home dir")

args = parser.parse_args()

site = args.site[0]
user = args.user[0]
site_home = os.path.join(SITE_HOME, site)
user_home = os.path.join(USER_HOME, user)
nginx_available_conf = os.path.join(NGINX_CONF_DIR, "sites-available", site + ".conf")
nginx_enabled_conf = os.path.join(NGINX_CONF_DIR, "sites-enabled", site + ".conf")
phppool_conf = os.path.join(PHPPOOL_CONF_DIR, site + ".conf")

# Template keys

template_keys = { 'user': user, 'site': site }

# Remove config files

print("Removing '" + nginx_available_conf + "'")
remove_if_exists(nginx_available_conf)

print("Removing '" + nginx_enabled_conf + "'")
remove_if_exists(nginx_enabled_conf)

print("Removing '" + phppool_conf + "'")
remove_if_exists(phppool_conf)

# Reload services

print "Reloading services"
reload_cmd = RELOAD_CMD.format(**template_keys)
os.system(reload_cmd)

# Clean user home or remove user

if args.remove_user:
    print("Removing user '" + user + "' and its home")
    delete_user_cmd = DELETE_USER_CMD.format(**template_keys)
    os.system(delete_user_cmd)
else:
    path = os.path.join(user_home, site);
    print("Removing symlink '" + path + "'")
    remove_if_exists(path);

# Remove site home

print("Removing site home '" + site_home + "'")
rmtree_if_exists(site_home + '/')
