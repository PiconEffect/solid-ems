#!/bin/bash

echo "==================================="
echo "   SOLID EMS INSTALL V10"
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
# Preserve existing optional values
# ----------------------------
OLD_SOLIS_INVERTER_ID=""

if [ -f .env ]
then
    OLD_SOLIS_INVERTER_ID=$(grep "^SOLIS_INVERTER_ID=" .env | cut -d "=" -f2-)
fi

# ----------------------------
# Solis API inputs
# ----------------------------
read -r -p "Solis Key ID: " SOLIS_KEY_ID

echo -n "Solis Key Secret: "
SOLIS_KEY_SECRET=""

while true
do
    IFS= read -r -s -n1 char

    if [[ -z "$char" ]]
    then
        echo ""
        break
    fi

    if [[ "$char" == $'\x7f' ]]
    then
        if [ -n "$SOLIS_KEY_SECRET" ]
        then
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
if [ -z "$SOLIS_KEY_ID" ] || [ -z "$SOLIS_KEY_SECRET" ]
then
    echo "ERROR: Missing Solis credentials"
    exit 1
fi

# ----------------------------
# Create .env
# ----------------------------
cat > .env <<ENVEOF
SOLIS_KEY_ID=$SOLIS_KEY_ID
SOLIS_KEY_SECRET=$SOLIS_KEY_SECRET

MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=30

BATTERY_CAPACITY_KWH=30
HISTORY_FILE=/data/solid_ems_history.json
HISTORY_DAYS=14
ENVEOF

# Preserve optional inverter ID if it existed
if [ -n "$OLD_SOLIS_INVERTER_ID" ]
then
    echo "" >> .env
    echo "SOLIS_INVERTER_ID=$OLD_SOLIS_INVERTER_ID" >> .env
    echo "Existing SOLIS_INVERTER_ID preserved"
fi

echo ".env created"
echo "Polling interval set to 30 seconds"
echo "AI history enabled"
echo ""

# ----------------------------
# Check Mosquitto config
# ----------------------------
mkdir -p mosquitto

if [ ! -f mosquitto/mosquitto.conf ]
then
    cat > mosquitto/mosquitto.conf <<MQTTEOF
listener 1883 0.0.0.0
allow_anonymous true

persistence true
persistence_location /mosquitto/data/

log_dest stdout
MQTTEOF

    echo "mosquitto.conf created"
else
    echo "mosquitto.conf already exists, keeping existing file"
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
``
