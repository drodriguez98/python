#!/bin/bash

# Elimina el archivo de la instalación de GLPI.

# Ruta al archivo de instalación
GLPI_INSTALL_FILE_PATH="/var/www/html/glpi/install/install.php"

# Verificar si el archivo de instalación de GLPI existe y eliminarlo si es necesario
if [ -f "$GLPI_INSTALL_FILE_PATH" ]; then
    rm "$GLPI_INSTALL_FILE_PATH"
    echo "El archivo de instalación $GLPI_INSTALL_FILE_PATH ha sido eliminado."
else
    echo "El archivo de instalación $GLPI_INSTALL_FILE_PATH ya se había eliminado previamente."
fi

# Reiniciar Apache
systemctl restart apache2
echo "Apache reiniciado."