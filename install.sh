#!/bin/bash

echo "==================================="
echo "   SOLID EMS INSTALL V5 (SMART)"
echo "==================================="
echo ""

# ----------------------------
# ✅ Vérification Docker
# ----------------------------
if ! command -v docker > /dev/null
then
    echo "❌ Docker non installé → installation..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "👉 Relance la session puis relance install.sh"
    exit 1
fi

echo "✅ Docker OK"
echo ""

# ----------------------------
# ✅ USERNAME
# ----------------------------
read -p "Solis Username (email): " SOLIS_USERNAME

# ----------------------------
# ✅ PASSWORD avec * + backspace
# ----------------------------
echo -n "Solis Password: "
SOLIS_PASSWORD=""

while true; do
    IFS= read -r -s -n1 char

    # Entrée
    if [[ $char == "" ]]; then
        echo ""
        break
    fi

    # Backspace
    if [[ $char == $'\x7f' ]]; then
        if [ -n "$SOLIS_PASSWORD" ]; then
            SOLIS_PASSWORD=${SOLIS_PASSWORD%?}
            echo -ne "\b \b"
        fi
    else
        SOLIS_PASSWORD+="$char"
        echo -n "*"
    fi
done

echo ""

# ----------------------------
# ✅ Vérification champs
# ----------------------------
if [ -z "$SOLIS_USERNAME" ] || [ -z "$SOLIS_PASSWORD" ]; then
  echo "❌ Champs vides → arrêt"
  exit 1
fi

# ----------------------------
# ✅ TEST LOGIN SOLIS
# ----------------------------
echo "🔍 Test connexion Solis..."

RESPONSE=$(curl -s -X POST "https://www.soliscloud.com:13333/v1/api/userLogin" \
  -H "Content-Type: application/json" \
  -d "{\"userInfo\":\"$SOLIS_USERNAME\",\"password\":\"$SOLIS_PASSWORD\"}")

SUCCESS=$(echo "$RESPONSE" | grep '"success":true')

if [ -z "$SUCCESS" ]; then
    echo ""
    echo "❌ Échec login Solis !"
    echo "👉 Vérifie ton email/mot de passe"
    echo "👉 Réponse API:"
    echo "$RESPONSE"
    exit 1
fi

echo "✅ Login Solis valide"
echo ""

# ----------------------------
# ✅ Création .env
# ----------------------------
cat <<EOF > .env
SOLIS_USERNAME=$SOLIS_USERNAME
SOLIS_PASSWORD=$SOLIS_PASSWORD
MQTT_HOST=mqtt
MQTT_PORT=1883
POLL_INTERVAL=3
EOF

echo "✅ .env créé"

# ----------------------------
# 🚀 Lancement Docker
# ----------------------------
echo ""
echo "🚀 Démarrage des services..."

docker compose down
docker compose up -d --build

# ----------------------------
# ✅ FIN
# ----------------------------
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "==================================="
echo "✅ INSTALLATION TERMINÉE ✅"
echo "==================================="
echo ""
echo "👉 Containers :"
echo "   docker ps"
echo ""
echo "👉 Logs :"
echo "   docker logs solid-core -f"
echo ""
echo "👉 Home Assistant :"
echo "   http://$IP:8123"
echo ""
