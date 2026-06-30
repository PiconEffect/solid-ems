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
# Hidden password input helper
# ----------------------------
read_secret() {
    local prompt="$1"
    local secret=""
    local char=""

    printf "%s" "$prompt" >&2

    while true
    do
        IFS= read -r -s -n1 char

        if [ -z "$char" ]
        then
            printf "\n" >&2
            break
        fi

        if [ "$char" = $'\177' ] || [ "$char" = $'\b' ]
        then
            if [ -n "$secret" ]
            then
                secret="${secret%?}"
                printf "\b \b" >&2
            fi
        else
            secret="${secret}${char}"
            printf "*" >&2
        fi
    done

    printf "%s" "$secret"
}

# ----------------------------
# Preserve existing optional values
# ----------------------------
OLD_SOLIS_INVERTER_ID=""
OLD_SOLIS_INVERTER_SN=""

if [ -f .env ]
then
    OLD_SOLIS_INVERTER_ID=$(grep "^SOLIS_INVERTER_ID=" .env | cut -d "=" -f2-)
    OLD_SOLIS_INVERTER_SN=$(grep "^SOLIS_INVERTER_SN=" .env | cut -d "=" -f2-)
fi

# ----------------------------
# Solis API inputs
# ----------------------------
read -r -p "Solis Key ID: " SOLIS_KEY_ID
SOLIS_KEY_SECRET=$(read_secret "Solis Key Secret: ")

echo ""

# ----------------------------
# Solis Cloud control inputs
# ----------------------------
read -r -p "Solis User Name: " SOLIS_USER_NAME
SOLIS_PASSWORD=$(read_secret "Solis Password: ")

echo ""

# ----------------------------
# Clean inputs
# ----------------------------
SOLIS_KEY_ID=$(printf "%s" "$SOLIS_KEY_ID" | tr -d '\r\n')
SOLIS_KEY_SECRET=$(printf "%s" "$SOLIS_KEY_SECRET" | tr -d '\r\n')
SOLIS_USER_NAME=$(printf "%s" "$SOLIS_USER_NAME" | tr -d '\r\n')
SOLIS_PASSWORD=$(printf "%s" "$SOLIS_PASSWORD" | tr -d '\r\n')

# ----------------------------
# Validation
# ----------------------------
if [ -z "$SOLIS_KEY_ID" ] || [ -z "$SOLIS_KEY_SECRET" ]
then
    echo "ERROR: Missing Solis API credentials"
    exit 1
fi

if [ -z "$SOLIS_USER_NAME" ] || [ -z "$SOLIS_PASSWORD" ]
then
    echo "WARNING: Missing Solis Cloud user/password."
    echo "Battery control login will not work until SOLIS_USER_NAME and SOLIS_PASSWORD are set."
fi

# ----------------------------
# Create .env
# ----------------------------
cat > .env <<ENVEOF
SOLIS_KEY_ID=$SOLIS_KEY_ID
SOLIS_KEY_SECRET=$SOLIS_KEY_SECRET

SOLIS_USER_NAME=$SOLIS_USER_NAME
SOLIS_PASSWORD=$SOLIS_PASSWORD

MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=10

BATTERY_CAPACITY_KWH=30
HISTORY_FILE=/data/solid_ems_history.json
HISTORY_DAYS=14

SOLIS_CONTROL_DRY_RUN=true
SOLIS_CONTROL_LANGUAGE=2
SOLIS_CONTROL_AUTO_VALIDATE=false
SOLIS_CONTROL_READ_SPACING_S=2.5
SOLIS_CONTROL_ALLOW_REAL_WRITE=false
SOLIS_CONTROL_ENABLE_MODE_PLAN=false
ENVEOF

# Preserve optional inverter ID if it existed
if [ -n "$OLD_SOLIS_INVERTER_ID" ]
then
    echo "" >> .env
    echo "SOLIS_INVERTER_ID=$OLD_SOLIS_INVERTER_ID" >> .env
    echo "Existing SOLIS_INVERTER_ID preserved"
fi

# Preserve optional inverter SN if it existed
if [ -n "$OLD_SOLIS_INVERTER_SN" ]
then
    echo "SOLIS_INVERTER_SN=$OLD_SOLIS_INVERTER_SN" >> .env
    echo "Existing SOLIS_INVERTER_SN preserved"
fi

echo ".env created"
echo "Polling interval set to 10 seconds"
echo "Solis battery control dry-run enabled"
echo "Solis battery control real write disabled"
echo "Solis battery control mode plan disabled"
echo "Solis battery control auto-validation disabled at startup"
echo "Solis control read spacing set to 2.5 seconds"
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
echo "  docker compose ps"
echo ""
echo "Check logs:"
echo "  docker compose logs solid-core -f"
echo ""
echo "Check Solis control env:"
echo "  docker compose exec solid-core sh -lc 'env | grep SOLIS_CONTROL'"
echo ""
echo "Home Assistant:"
echo "  http://$IP:8123"
echo ""
