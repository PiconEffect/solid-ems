SOLID EMS V10 - fichiers textes propres

Ces fichiers texte contiennent les versions completes a copier dans GitHub.
Ils sont separes par fonction/fichier pour eviter les collages partiels qui ont corrompu le repo.

Ordre de remplacement recommande dans GitHub :
1. install.sh
2. docker-compose.yml
3. services/core/app/main.py
4. services/core/app/discovery.py
5. services/core/app/solis_client.py
6. services/core/app/tempo.py
7. services/core/app/ai_engine.py

Important :
- Dans GitHub, ouvre le fichier, fais CTRL+A, supprime tout, colle le contenu complet du fichier texte correspondant.
- Ne fais pas de remplacement partiel.
- Ne colle aucun <br>.

Commandes de verification apres clone :

bash -n install.sh
python3 -m py_compile services/core/app/main.py
python3 -m py_compile services/core/app/discovery.py
python3 -m py_compile services/core/app/solis_client.py
python3 -m py_compile services/core/app/tempo.py
python3 -m py_compile services/core/app/ai_engine.py
docker compose config

grep -R "importisponible" -n .
grep -R "publish_discovery_dc_power" -n .
grep -R "<br>" -n .
grep -R "I | awk" -n .
