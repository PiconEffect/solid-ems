#!/bin/bash

echo "==================================="
echo "      SOLID EMS INSTALL V4"
echo "==================================="
echo ""

# ----------------------------
# ✅ Vérification Docker
# ----------------------------
if ! command -v docker &> /dev/null
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
# ✅ Demande identifiants
# ----------------------------
read -p "Solis Username (email): " SOLIS_USERNAME
read -s -p "Solis Password: " SOLIS_PASSWORD
echo ""
echo ""

# ----------------------------
# ⚠️ Validation simple
# ----------------------------
if [ -z "$SOLIS_USERNAME" ] || [ -z "$SOLIS_PASSWORD" ]; then
  echo "❌ Champs vides → arrêt"
  exit 1
fi

# ----------------------------
# ✅ Création du .env
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
echo "🚀 Lancement des services..."

docker compose down
docker compose up -d --build

# ----------------------------
# ✅ Résultat
# ----------------------------
echo ""
echo "✅ Installation terminée !"
echo ""
echo "👉 Vérifie avec : docker ps"
echo "👉 Logs : docker logs solid-core -f"
echo ""
