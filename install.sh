#!/bin/bash

echo "==================================="
I | awk '{print $1}')echo "   SOLID EMS INSTALL V10"

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
echo "==================================="
echo ""

# ----------------------------
# Check Docker
# ----------------------------
if ! command -v docker > /dev/null
then
    echo "Docker not found -> installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "Please reconnect SSH then rerun install.sh"
    exit 1
fi

echo "Docker OK"
echo ""

# ----------------------------
# Solis API inputs
# ----------------------------
read -r -p "Solis Key ID: " SOLIS_KEY_ID

echo -n "Solis Key Secret: "
SOLIS_KEY_SECRET=""

while true; do
    IFS= read -r -s -n1 char

    # Enter key
    if [[ -z "$char" ]]; then
        echo ""
        break
    fi

    # Backspace
    if [[ "$char" == $'\x7f' ]]; then
        if [ -n "$SOLIS_KEY_SECRET" ]; then
            SOLIS_KEY_SECRET="${SOLIS_KEY_SECRET%?}"
            echo -ne "\b \b"
        fi
    else
        SOLIS_KEY_SECRET="${SOLIS_KEY_SECRET}${char}"
        echo -n "*"
    fi
done

echo ""

# ----------------------------
# Clean inputs
# Avoid terminal paste artefacts like ^[[201~
# ----------------------------
SOLIS_KEY_ID=$(printf "%s" "$SOLIS_KEY_ID" | tr -cd '0-9')
SOLIS_KEY_SECRET=$(printf "%s" "$SOLIS_KEY_SECRET" | tr -cd 'A-Za-z0-9')

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
cat > .env <<EOF
SOLIS_KEY_ID=$SOLIS_KEY_ID
SOLIS_KEY_SECRET=$SOLIS_KEY_SECRET

MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=30

BATTERY_CAPACITY_KWH=30
HISTORY_FILE=/data/solid_ems_history.json
HISTORY_DAYS=14
EOF

echo ".env created"
echo "Polling interval set to 30 seconds"
echo "AI history enabled"
echo ""

# ----------------------------
# Check Mosquitto config
# ----------------------------
mkdir -p mosquitto

if [ ! -f mosquitto/mosquitto.conf ]; then
    cat > mosquitto/mosquitto.conf <<EOF
listener 1883 0.0.0.0
allow_anonymous true

persistence true
persistence_location /mosquitto/data/

log_dest stdout
EOF
    echo "mosquitto.conf created"
fi

# ----------------------------
# Start services
# ----------------------------
echo "Starting containers..."

docker compose down
docker compose up -d --build

# ----------------------------
# End
# ----------------------------
