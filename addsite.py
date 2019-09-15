#!/usr/bin/env python
import argparse, re, socket, sys, os, pwd, grp
import config

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
        return True
    except socket.error:
        return False

def is_correct_user_name(user):
    return re.match("^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$", user)

###############################################################################
# Parse arguments

parser = argparse.ArgumentParser(description = 'Add new site.')

parser.add_argument('--site', type=str, nargs=1, required=True,
                    help='Site domain')

parser.add_argument('--user', type=str, nargs=1, required=True,
                    help='User owns this site')

parser.add_argument('--wwwuser', type=str, nargs=1, default=[ config.default_wwwuser ],
                    help="www user (default: '" + config.default_wwwuser + "'")

parser.add_argument('--wwwgroup', type=str, nargs=1, default=[ config.default_wwwgroup ],
                    help="www group (default: '" + config.default_wwwgroup + "'")

parser.add_argument('--php', action='store_true',
                    help='Enable PHP')

parser.add_argument('--phpver', type=str, nargs=1, default=[ config.default_phpver ],
                    help="PHP Version (default: '" + config.default_phpver + "'")

parser.add_argument('--create-user', action='store_true',
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
nginx_conf = config.nginx_conf.format(**keys)
phppool_conf = config.phppool_conf.format(**keys)
logrotate_conf = config.logrotate_conf.format(**keys)
create_user_cmd = config.create_user_cmd.format(**keys)
delete_user_cmd = config.delete_user_cmd.format(**keys)
reload_cmd = config.reload_cmd.format(**keys)

uid = get_uid(user)
gid = get_gid(group)
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

if not os.path.isdir(os.path.dirname(nginx_conf)):
    sys.exit("Directory '" + os.path.dirname(nginx_conf) + "' does not exist")

if args.php and not os.path.isdir(os.path.dirname(phppool_conf)):
    sys.exit("Directory '" + os.path.dirname(phppool_conf) + "' does not exist")

# Check root rights

if not is_root():
  sys.exit("Please, run as root")

###############################################################################
# Choose template and set template keys

if args.php:
  template = 'nginx-php';
else:
  template = 'nginx-nophp'

template_keys = {
    'template': template,
    'site': site,
    'user': user,
    'group': group,
    'wwwuser': wwwuser,
    'wwwgroup': wwwgroup,
    'phpver': phpver,
    'site_home': site_home,
    'user_home': user_home,
    'backup_dir': backup_dir
}

###############################################################################
# Create user if nessesary

if args.create_user:
    os.system(create_user_cmd)
    uid = get_uid(user)
    gid = get_gid(group)
    if uid is None: sys.exit("Cannot create user '" + user + "'")
    if gid is None: sys.exit("Cannot create group '" + group + "'")
    recursive_chmod(user_home, 0o640, 0o750)

if not os.path.exists(backup_dir):
    os.mkdir(backup_dir, 0o700)
    os.chown(backup_dir, uid, gid);

###############################################################################
# Instantiate template

os.mkdir(site_home)
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', template))
for dirpath, dirnames, filenames in os.walk('.'):
    for dirname in dirnames:
        os.mkdir(os.path.join(site_home, dirpath, dirname))
    for filename in filenames:
        if filename == '.emptydir': continue
        src = os.path.join(dirpath, filename)
        dst = os.path.join(site_home, dirpath, filename)
        t = open(src, 'r').read()
        t = t.format(**template_keys)
        open(dst, 'w').write(t)

# Site home: root:{group} 770
recursive_chown(site_home, 0, gid)
recursive_chmod(site_home, 0o660, 0o770)

# public_html: {user}:{group} 750
recursive_chown(os.path.join(site_home, 'public_html'), uid, gid)
recursive_chmod(os.path.join(site_home, 'public_html'), 0o640, 0o750)

# nginx.conf: root:{group} 640
os.chmod(os.path.join(site_home, 'nginx.conf'), 0o640)

# phppool.conf: root:{group} 640
if args.php:
    os.chmod(os.path.join(site_home, 'backup.sh'), 0o640)

###############################################################################
# Link config files

if os.path.lexists(nginx_conf): os.unlink(nginx_conf)
os.symlink(os.path.join(site_home, 'nginx.conf'), nginx_conf)

if os.path.lexists(logrotate_conf): os.unlink(logrotate_conf)
os.symlink(os.path.join(site_home, 'logrotate'), logrotate_conf)

if args.php:
    if os.path.lexists(phppool_conf): os.unlink(phppool_conf)
    os.symlink(os.path.join(site_home, 'phppool.conf'), phppool_conf)

###############################################################################
# Link site home to user home

os.symlink(site_home, os.path.join(user_home, site))

###############################################################################
# Reload services

print "Reloading services"
os.system(reload_cmd)
