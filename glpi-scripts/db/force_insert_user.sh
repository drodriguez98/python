CONFIG_FILE="/etc/glpi/config_db.php" && \
DB_USER=$(grep "\$dbuser" $CONFIG_FILE | awk -F"'" '{print $2}') && \
DB_PASS=$(grep "\$dbpassword" $CONFIG_FILE | awk -F"'" '{print $2}') && \
DB_NAME=$(grep "\$dbdefault" $CONFIG_FILE | awk -F"'" '{print $2}') && \
DB_HOST=$(grep "\$dbhost" $CONFIG_FILE | awk -F"'" '{print $2}') && \
mysql -u"$DB_USER" -p"$DB_PASS" -h "$DB_HOST" "$DB_NAME" -e "
INSERT INTO glpi_users (name, password, password_last_update, phone, realname, firstname, is_active, authtype, date_mod, profiles_id, entities_id) VALUES ('diego.rodriguez', '\$2y\$10\$xNI55RgtV4ScFV43cvBza.2iV1tqWgGtguADLux/nyILmAQqXVFHm', '2022-05-15 10:41:37', '986101000', 'Rodríguez Barros', 'Diego', 1, 1, '2024-09-13 10:41:37', 4, 0); 
INSERT INTO glpi_profiles_users (users_id, profiles_id, entities_id, is_recursive, is_dynamic, is_default_profile) VALUES (LAST_INSERT_ID(), 4, 0, 1, 0, 0);