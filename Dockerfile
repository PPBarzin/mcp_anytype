# Étape 1 : Choisir une image de base Python légère et moderne
FROM python:3.11-slim

# Étape 2 : Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Étape 3 : Installer les dépendances
# On copie d'abord uniquement le fichier des dépendances pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Étape 4 : Copier le reste du code de l'application
# L'ordre est important pour l'optimisation du cache
COPY . .

# Étape 5 : Exposer le port sur lequel l'application écoute
EXPOSE 1621

# Étape 6 : Définir la commande pour lancer le serveur
# Note: On n'utilise pas --reload dans une image Docker de production.
# On utilise la variable d'environnement PORT si elle est définie, sinon 1621.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "1621"]
