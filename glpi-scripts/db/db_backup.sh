#!/bin/bash

# GLPI database backup

DB_USER="glpi_user"
DB_PASS="glpi"
DB_NAME="glpidb"
BACKUP_DIR="/var/backups/glpi"

mkdir -p $BACKUP_DIR
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/glpi_backup_$(date +%F).sql