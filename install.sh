#!/bin/bash

echo "==================================="
echo "   SOLID EMS INSTALL V6 (API PRO)"
echo "==================================="
echo ""

# ----------------------------
# ✅ Vérification Docker
# ----------------------------
if ! command -v docker > /dev/null
then
    echo "Docker not found -> installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Reconnect SSH then relaunch install.sh"
    exit 1
fi

echo "Docker OK"
echo ""

# ----------------------------
# ✅ INPUT SOLIS API
# ----------------------------
read -p "Solis Key ID: " SOLIS_KEY_ID
read -p "Solis Key Secret: " SOLIS_KEY_SECRET
read -p "Solis Inverter ID: " SOLIS_INVERTER_ID

echo ""

# ----------------------------
# ✅ VALIDATION
# ----------------------------
if [ -z "$SOLIS_KEY_ID" ] || [ -z "$SOLIS_KEY_SECRET" ] || [ -z "$SOLIS_INVERTER_ID" ]; then
  echo "ERROR: missing input"
  exit 1
fi

# ----------------------------
# ✅ CREATE .env
# ----------------------------
cat <<EOF > .env
SOLIS_KEY_ID=$SOLIS_KEY_ID
SOLIS_KEY_SECRET=$SOLIS_KEY_SECRET
SOLIS_INVERTER_ID=$SOLIS_INVERTER_ID

MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=3
EOF

echo ".env created"

# ----------------------------
# 🚀 START
# ----------------------------
echo ""
echo "Starting services..."

docker compose down
docker compose up -d --build

# ----------------------------
# ✅ FIN
# ----------------------------
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "==================================="
echo "INSTALL DONE"
echo "==================================="
echo ""
echo "docker ps"
echo "docker logs solid-core -f"
echo ""
echo "Home Assistant:"
echo "http://$IP:8123"
echo ""
