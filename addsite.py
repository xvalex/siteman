#!/usr/bin/env python
import argparse, re, socket, sys, os, pwd, grp
from config import *

def is_root():
    """Check admin permissions."""
    return os.geteuid() == 0

def get_gid(name):
    """Returns a gid, given a group name."""
    try:
        result = grp.getgrnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None

def get_uid(name):
    """Returns an uid, given a user name."""
    try:
        result = pwd.getpwnam(name)
    except KeyError:
        result = None
    if result is not None:
        return result[2]
    return None

def recursive_chown(path, uid, gid):
    os.chown(path, uid, gid)
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for dname in dirnames:
                os.chown(os.path.join(dirpath, dname), uid, gid)
            for fname in filenames:
                os.chown(os.path.join(dirpath, fname), uid, gid)

def recursive_chmod(path, file_mode, dir_mode):
    if os.path.isdir(path):
        os.chmod(path, dir_mode)
        for dirpath, dirnames, filenames in os.walk(path):
            for dname in dirnames:
                os.chmod(os.path.join(dirpath, dname), dir_mode)
            for fname in filenames:
                os.chmod(os.path.join(dirpath, fname), file_mode)
    else:
        os.chmod(path, file_mode)


def can_resolve(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.error:
        return 0

def is_correct_user_name(user):
    return re.match("^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$", user)

def instantiate_template(template, dest, keys):
    t = open(template, 'r').read()
    t = t.format(**keys)
    open(dest, 'w').write(t)

###############################################################################
# Parse arguments

parser = argparse.ArgumentParser(description = 'Add new site.')

parser.add_argument('--site', type=str, nargs=1, required=True,
                    help='Site domain')

parser.add_argument('--user', type=str, nargs=1, required=True,
                    help='User owns this site')

parser.add_argument('--wwwuser', type=str, nargs=1, default=[ WWWUSER ],
                    help="www user (default: '" + WWWUSER + "'")

parser.add_argument('--wwwgroup', type=str, nargs=1, default=[ WWWGROUP ],
                    help="www group (default: '" + WWWGROUP + "'")

parser.add_argument('--php', action='store_true',
                    help='Enable PHP')

parser.add_argument('--create-user', action='store_true',
                    help='Create new user for this site')

parser.add_argument('--get-cert', action='store_true',
                    help="Acquire Let's Encrypt certificate for this site")

args = parser.parse_args()

site = args.site[0]
user = args.user[0]
wwwuser = args.wwwuser[0]
wwwgroup = args.wwwgroup[0]
site_home = os.path.join(SITE_HOME, site)
user_home = os.path.join(USER_HOME, user)
site_nginx_conf = os.path.join(site_home, 'nginx.conf')
site_phppool_conf = os.path.join(site_home, 'phppool.conf')
nginx_available_conf = os.path.join(NGINX_CONF_DIR, "sites-available", site + ".conf")
nginx_enabled_conf = os.path.join(NGINX_CONF_DIR, "sites-enabled", site + ".conf")
phppool_conf = os.path.join(PHPPOOL_CONF_DIR, site + ".conf")

backup_dir = os.path.join(user_home, "backup")
backup_script = os.path.join(site_home, 'backup.sh')

uid = get_uid(user)
wwwuid = get_uid(wwwuser)
wwwgid = get_gid(wwwgroup)


###############################################################################
# Check parameters

if args.create_user and not is_correct_user_name(user):
    sys.exit("Invalid user name '" + user + "'")

if not args.create_user and uid is None:
    sys.exit("User '" + user + "' does not exist")

if os.path.lexists(user_home):
    if args.create_user: sys.exit("User home '" + user_home + "' already exist")
else:
    if not args.create_user: sys.exit("User home '" + user_home + "' not found")

if wwwuid is None:
    sys.exit("User '" + wwwuser + "' does not exist")

if wwwgid is None:
    sys.exit("Group '" + wwwgroup + "' does not exist")

if not can_resolve(site):
    sys.exit("Cannot resolve '" + site + "'")

if os.path.lexists(site_home):
    sys.exit("Site home '" + site_home + "' already exist")

if not os.path.lexists(os.path.join(NGINX_CONF_DIR, "sites-available")):
    sys.exit("'" + os.path.join(NGINX_CONF_DIR, "sites-available") + "' does not exist")

if not os.path.lexists(os.path.join(NGINX_CONF_DIR, "sites-enabled")):
    sys.exit("'" + os.path.join(NGINX_CONF_DIR, "sites-enabled") + "' does not exist")

if os.path.lexists(nginx_available_conf):
    sys.exit("Config file '" + nginx_available_conf + "' already exist")

if os.path.lexists(nginx_enabled_conf):
    sys.exit("Config file '" + nginx_enabled_conf + "' already exist")

if args.php and not os.path.lexists(PHPPOOL_CONF_DIR):
    sys.exit("'" + PHPPOOL_CONF_DIR + "' does not exist")

if args.php and os.path.lexists(phppool_conf):
    sys.exit("Config file '" + phppool_conf + "' already exist")

# Check root rights

if not is_root():
  sys.exit("Please, run as root")

###############################################################################
# Template keys

template_keys = {
    'site': site,
    'user': user,
    'wwwuser': wwwuser,
    'wwwgroup': wwwgroup,
    'site_home': site_home,
    'user_home': user_home,
    'backup_dir': backup_dir
}

###############################################################################
# Create user if nessesary

if args.create_user:
    create_user_cmd = CREATE_USER_CMD.format(**template_keys)
    os.system(create_user_cmd)
    uid = get_uid(user)
    if uid is None:
        sys.exit("Cannot create user '" + user + "'")
    recursive_chmod(user_home, 0o640, 0o750)

if not os.path.exists(backup_dir):
    os.mkdir(backup_dir, 0o700) # Owner-only access

###############################################################################
# Create site root

os.mkdir(site_home, 0o750)
os.mkdir(os.path.join(site_home, "public_html"), 0o750) # Read-only www access
os.mkdir(os.path.join(site_home, "logs"), 0o770)        # Allow www write access

instantiate_template(os.path.join('templates', 'backup.sh'),
                     backup_script, template_keys)
os.chmod(backup_script, 0o700)

if args.php:
    instantiate_template(os.path.join('templates', 'nginx.enablephp.conf'),
                         site_nginx_conf, template_keys)
    instantiate_template(os.path.join('templates', 'phppool.conf'),
                         site_phppool_conf, template_keys)
    instantiate_template(os.path.join('templates', 'index.php'),
                         os.path.join(site_home, 'public_html', 'index.php'), template_keys)
    os.chmod(site_nginx_conf, 0o700)
    os.chmod(phppool.conf, 0o700)
else:
    instantiate_template(os.path.join('templates', 'nginx.nophp.conf'),
                         site_nginx_conf, template_keys)
    instantiate_template(os.path.join('templates', 'index.html'),
                         os.path.join(site_home, 'public_html', 'index.html'), template_keys)
    os.chmod(site_nginx_conf, 0o700)

recursive_chown(site_home, uid, wwwgid)

###############################################################################
# Link config files

os.symlink(site_nginx_conf, nginx_available_conf)
os.chown(nginx_available_conf, uid, wwwgid);

os.symlink(site_nginx_conf, nginx_enabled_conf)
os.chown(nginx_enabled_conf, uid, wwwgid);

if args.php:
    os.symlink(site_phppool_conf, phppool_conf)
    os.chown(phppool_conf, uid, wwwgid);

###############################################################################
# Link site home to user home

os.symlink(site_home, os.path.join(user_home, site))
os.chown(os.path.join(user_home, site), uid, wwwgid);

###############################################################################
# Reload services

print "Reloading services"
reload_cmd = RELOAD_CMD.format(**template_keys)
os.system(reload_cmd)
