#!/bin/bash

echo "==================================="
echo "   SOLID EMS INSTALL V7 (AUTO)"
echo "==================================="
echo ""

# ----------------------------
# Check Docker
# ----------------------------
if ! command -v docker > /dev/null
then
    echo "Docker not found -> installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Please reconnect SSH then rerun install.sh"
    exit 1
fi

echo "Docker OK"
echo ""

# ----------------------------
# Solis API inputs
# ----------------------------
read -p "Solis Key ID: " SOLIS_KEY_ID
read -p "Solis Key Secret: " SOLIS_KEY_SECRET

echo ""

# ----------------------------
# Validation
# ----------------------------
if [ -z "$SOLIS_KEY_ID" ] || [ -z "$SOLIS_KEY_SECRET" ]; then
  echo "ERROR: Missing Solis credentials"
  exit 1
fi

# ----------------------------
# Create .env
# ----------------------------
cat <<EOF > .env
SOLIS_KEY_ID=$SOLIS_KEY_ID
SOLIS_KEY_SECRET=$SOLIS_KEY_SECRET

MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=30
EOF

echo ".env created"
echo "Polling interval set to 30 seconds"
echo ""

# ----------------------------
# Start services
# ----------------------------
echo "Starting containers..."

docker compose down
docker compose up -d --build

# ----------------------------
# End
# ----------------------------
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "==================================="
echo "INSTALL DONE"
echo "==================================="
echo ""
echo "Check containers:"
echo "  docker ps"
echo ""
echo "Check logs:"
echo "  docker logs solid-core -f"
echo ""
echo "Home Assistant:"
echo "  http://$IP:8123"
echo ""
