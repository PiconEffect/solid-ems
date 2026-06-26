#!/bin/bash

echo "====== SOLID EMS INSTALL ======"

# Vérif Docker
if ! command -v docker &> /dev/null
then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Reboot and relaunch"
    exit 1
fi

# Demande utilisateur
read -p "Solis Username: " SOLIS_USERNAME
read -s -p "Solis Password: " SOLIS_PASSWORD
echo ""

# Création .env
cat <<EOF > .env
SOLIS_USERNAME=$SOLIS_USERNAME
SOLIS_PASSWORD=$SOLIS_PASSWORD
MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=3
EOF

# Lancement
docker compose up -d --build

echo "✅ Installation terminée"
