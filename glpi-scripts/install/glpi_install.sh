#!/bin/bash

# https://faq.teclib.com/03_knowledgebase/procedures/install_glpi/

echo "Actualizando el sistema..."
apt update && apt upgrade -y

echo "Instalando Apache y PHP..."
apt install -y apache2 php php-{apcu,cli,common,curl,gd,imap,ldap,mysql,xmlrpc,xml,mbstring,bcmath,intl,zip,redis,bz2} libapache2-mod-php php-soap php-cas

echo "Instalando MariaDB..."
apt install -y mariadb-server

echo "Configurando MariaDB (mysql_secure_installation automático)..."
mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY 'abc123.';  # Cambia 'abc123.' por tu contraseña de root
DELETE FROM mysql.user WHERE User='root' AND Host!='localhost';
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test_%';
FLUSH PRIVILEGES;
EOF
echo "MariaDB configurado con éxito."

echo "Importando zonas horarias en MariaDB..."
mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p'abc123.' mysql

echo "Creando base de datos y usuario para GLPI..."
mysql -u root -p'abc123.' <<EOF
CREATE DATABASE glpi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'glpi'@'localhost' IDENTIFIED BY 'abc123.';  # Cambia 'abc123.' por tu contraseña de usuario GLPI
GRANT ALL PRIVILEGES ON glpi.* TO 'glpi'@'localhost';
GRANT SELECT ON mysql.time_zone_name TO 'glpi'@'localhost';
FLUSH PRIVILEGES;
EOF
echo "Base de datos y usuario para GLPI creados."

echo "Descargando y descomprimiendo GLPI..."
cd /var/www/html
wget https://github.com/glpi-project/glpi/releases/download/10.0.16/glpi-10.0.16.tgz
tar -xvzf glpi-10.0.16.tgz

echo "Configurando downstream.php..."
echo "<?php
    define('GLPI_CONFIG_DIR', '/etc/glpi/');
    if (file_exists(GLPI_CONFIG_DIR . '/local_define.php')) {
        require_once GLPI_CONFIG_DIR . '/local_define.php';
    }" >> /var/www/html/glpi/inc/downstream.php

echo "Moviendo archivos de GLPI a las ubicaciones adecuadas..."
mv /var/www/html/glpi/config /etc/glpi
mv /var/www/html/glpi/files /var/lib/glpi
mv /var/lib/glpi/_log /var/log/glpi

echo "Creando el archivo local_define.php..."
echo "<?php
    define('GLPI_VAR_DIR', '/var/lib/glpi');
    define('GLPI_DOC_DIR', GLPI_VAR_DIR);
    define('GLPI_CRON_DIR', GLPI_VAR_DIR . '/_cron');
    define('GLPI_DUMP_DIR', GLPI_VAR_DIR . '/_dumps');
    define('GLPI_GRAPH_DIR', GLPI_VAR_DIR . '/_graphs');
    define('GLPI_LOCK_DIR', GLPI_VAR_DIR . '/_lock');
    define('GLPI_PICTURE_DIR', GLPI_VAR_DIR . '/_pictures');
    define('GLPI_PLUGIN_DOC_DIR', GLPI_VAR_DIR . '/_plugins');
    define('GLPI_RSS_DIR', GLPI_VAR_DIR . '/_rss');
    define('GLPI_SESSION_DIR', GLPI_VAR_DIR . '/_sessions');
    define('GLPI_TMP_DIR', GLPI_VAR_DIR . '/_tmp');
    define('GLPI_UPLOAD_DIR', GLPI_VAR_DIR . '/_uploads');
    define('GLPI_CACHE_DIR', GLPI_VAR_DIR . '/_cache');
    define('GLPI_LOG_DIR', '/var/log/glpi');" >> /etc/glpi/local_define.php

echo "Configurando permisos de carpetas y archivos..."
chown root:root /var/www/html/glpi/ -R
chown www-data:www-data /etc/glpi -R
chown www-data:www-data /var/lib/glpi -R
chown www-data:www-data /var/log/glpi -R
chown www-data:www-data /var/www/html/glpi/marketplace -Rf
find /var/www/html/glpi/ -type f -exec chmod 0644 {} \;
find /var/www/html/glpi/ -type d -exec chmod 0755 {} \;
find /etc/glpi -type f -exec chmod 0644 {} \;
find /etc/glpi -type d -exec chmod 0755 {} \;
find /var/lib/glpi -type f -exec chmod 0644 {} \;
find /var/lib/glpi -type d -exec chmod 0755 {} \;
find /var/log/glpi -type f -exec chmod 0644 {} \;
find /var/log/glpi -type d -exec chmod 0755 {} \;
echo "Permisos configurados correctamente."

echo "Configurando VirtualHost de Apache para GLPI..."
echo "
    # Configuración del VirtualHost para el puerto 80
    <VirtualHost *:80>
        ServerName yourglpi.yourdomain.com
        DocumentRoot /var/www/html/glpi/public
        <Directory /var/www/html/glpi/public>
            Require all granted
            RewriteEngine On
            RewriteCond %{HTTP:Authorization} ^(.+)$
            RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
            RewriteCond %{REQUEST_FILENAME} !-f
            RewriteRule ^(.*)$ index.php [QSA,L]
        </Directory>
    </VirtualHost>" >> /etc/apache2/sites-available/glpi.conf

echo "Deshabilitando el sitio por defecto de Apache y habilitando el nuevo sitio GLPI..."
a2dissite 000-default.conf
a2enmod rewrite
a2ensite glpi.conf
systemctl restart apache2
echo "Apache configurado correctamente."

echo "Modificando configuración en php.ini..."
# Ruta al archivo php.ini
PHP_INI_PATH="/etc/php/8.3/apache2/php.ini"

# Configuraciones de PHP a modificar
declare -A CONFIG_CHANGES=(
    ["memory_limit"]="512M"
    ["file_uploads"]="On"
    ["max_execution_time"]="600"
    ["session.auto_start"]="Off"
    ["session.use_trans_sid"]="0"
    ["session.cookie_httponly"]="On"
)

# Realizar un backup del archivo php.ini
cp $PHP_INI_PATH $PHP_INI_PATH.bak

# Aplicar cambios en php.ini
for key in "${!CONFIG_CHANGES[@]}"; do
    sed -i "s|^${key} =.*|${key} = ${CONFIG_CHANGES[$key]}|I" "$PHP_INI_PATH"
done

echo "Configuración de $PHP_INI_PATH actualizada."

echo "Reiniciando servicios..."
systemctl restart apache2
systemctl restart mariadb
echo "Servicios reiniciados correctamente."

echo "Instalación de GLPI completada. Accede a la interfaz web para finalizar la configuración."
