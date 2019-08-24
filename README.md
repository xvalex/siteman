# SiteMan
Manage multiple www sites at a single host. Creates basic file and directory structures from templates.

File and directory layout:

* /etc/nginx/sites-avalable/$site.conf - Link to /var/www/$site/nginx.conf
* /etc/nginx/sites-enabled/$site.conf - Link to /var/www/$site/nginx.conf
* /etc/php/7.2/fpm/pool.d/$site.conf - Link to /var/www/$site/phppool.conf

* /home/$user	- User home
* /home/$user/$site - Link to /var/www/$site
* /home/$user/backup - Backups

* /var/www/$site - Site home
* /var/www/$site/public_html - www root
* /var/www/$site/backup.sh - Backup script
* /var/www/$site/nginx.conf - nginx config file
* /var/www/$site/phppool.conf - PHP pool configuration
* /var/www/$site/logs - Logs dir
* /var/www/$site/logs/access.log - nginx access log (nginx template)
* /var/www/$site/logs/error.log - nginx error log (nginx template)
