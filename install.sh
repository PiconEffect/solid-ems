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
# ✅ Demande USERNAME
# ----------------------------
read -p "Solis Username (email): " SOLIS_USERNAME

# ----------------------------
# ✅ PASSWORD avec *
# ----------------------------
echo -n "Solis Password: "
SOLIS_PASSWORD=""

while IFS= read -r -s -n1 char; do
    if [[ $char == "" ]]; then
        echo ""
        break
    fi
    SOLIS_PASSWORD+="$char"
    echo -n "*"
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
echo ""
echo "✅ Installation terminée ✅"
echo ""
echo "👉 docker ps"
echo "👉 docker logs solid-core -f"
echo ""
