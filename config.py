# Default values

default_wwwuser		= 'www-data'
default_wwwgroup	= 'www-data'
default_phpver		= '7.2'

###############################################################################
# Parametrized values.
#
# Parameters:
# * {user} - User name (example: 'jdoe')
# * {group} - User primary group, normally equals to {user} (example: 'jdoe')
# * {wwwuser} - www user (example: 'www-data')
# * {wwwgroup} - www user (example: 'www-data')
# * {phpver} - PHP version (example: '7.2')

user_home		= '/home/{user}'
site_home		= '/var/www/{site}'
backup_dir		= '/home/{user}/wwwbackup'
phppool_conf		= '/etc/php/{phpver}/fpm/pool.d/{site}.conf'
nginx_conf		= '/etc/nginx/sites-enabled/{site}.conf'
create_user_cmd		= 'adduser --quiet --disabled-password --gecos "User for managing {site}" {user}; adduser --quiet {wwwuser} {group}'
delete_user_cmd 	= 'deluser --quiet {wwwuser} {group}; deluser --quiet --remove-home {user}'
reload_cmd		= 'systemctl reload php{phpver}-fpm; systemctl reload nginx'
