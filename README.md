# SiteMan
Manage multiple www sites at a single host.

Creates basic file and directory structures from templates. Users are isolated from each other. One user may own several sites.

## Quick start

You must have a working domain before adding a site.

```Shell
# apt install python nginx php7.2 php7.2-fpm php7.2-common php7.2-cli curl
# git clone https://github.com/xvalex/siteman.git
# python siteman/addsite.py --user www-test --site test.example.com --create-user --php
# curl -Is http://test.example.com | head -1
HTTP/1.1 200 OK
```

## Default config

Default file and directory layout:

| Name                         | Permissions              | Descrpition            |
|------------------------------|--------------------------|------------------------|
| **User home**                |                          |                        |
| /home/{user}                 | {user}:{group} 750       | User home              |
| /home/{user}/{site}          |                          | Link to site home      |
| /home/{user}/wwwbackup       | {user}:{group} 700       | Backups                |
| **Site home**                |                          |                        |
| /var/www/{site}              | root:{group} 770         | Site home              |
| /var/www/{site}/logs         | root:{group} 770         | Logs (nginx, php, etc) |
| /var/www/{site}/public_html  | {user}:{group} 750       | www root               |
| /var/www/{site}/backup.sh    | {user}:{group} 700       | Backup script          |
| /var/www/{site}/logrotate    | root:{group} 740         | Logrotate config       |
| /var/www/{site}/nginx.conf   | root:{group} 640         | Nginx config file      |
| /var/www/{site}/phppool.conf | root:{group} 640         | PHP pool config file   |

Configuration files:

| Config file                              | Links to                     |
|------------------------------------------|------------------------------|
| /etc/nginx/sites-enabled/{site}.conf     | /var/www/{site}/nginx.conf   |
| /etc/php/{phpver}/fpm/pool.d/{site}.conf | /var/www/{site}/phppool.conf |
| /etc/logrotate.d/{site}                  | /var/www/{site}/logrotate    |

