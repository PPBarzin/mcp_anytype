# Serveur MCP pour Anytype

Ce projet implémente un serveur MCP (Model Context Protocol) en Python pour interagir avec une instance **Anytype locale**. Il expose l'API REST officielle d'Anytype (v1) sous forme d'outils MCP, avec **deux transports** (SSE et Streamable HTTP) afin d'être utilisable directement par différents clients agentic (Claude Code, Codex, Antigravity, etc.) sans dépendre du paquet officiel `@anyproto/anytype-mcp`.

L'intérêt de centraliser via ce serveur plutôt que de connecter chaque client directement à l'API locale d'Anytype :
- **Un seul point de configuration** (URL, token, version d'API) pour tous tes agents.
- **Rotation de clé simplifiée** : un seul endroit à mettre à jour (le container) au lieu de la dupliquer dans la config de chaque outil.
- **Activation à la carte** : chaque projet/agent déclare (ou non) ce serveur MCP, sans dépendre d'un paquet lancé en local par chaque client.

## Fonctionnalités

Le serveur expose l'API Anytype sous forme de 53 outils, organisés en 11 catégories. **Couverture complète : 52/52 opérations du spec officiel v1** (2025-11-08).

**Note sur la suppression** : l'API Anytype "supprime" un objet/property/tag/type en l'archivant (`archived: true`), ce n'est pas une suppression définitive. Autre particularité observée : la réponse immédiate d'un appel `delete-*` peut encore afficher `archived: false` — un `get-*` juste après confirme le vrai état.

### 1. Recherche et récupération (pattern RAG classique)
Convention `search` / `fetch` utile pour tout système qui suit le modèle "chercher puis récupérer le détail" (RAG, agents génériques, etc.).

- **`search`** (`search-global`) : Recherche des objets dans tous les "spaces".
- **`fetch`** : Récupère le contenu complet d'un objet à partir d'un ID composite (`space_id/object_id`) fourni par l'outil de recherche.

### 2. Gestion des "Spaces"
- **`list-spaces`**: Liste les "spaces" accessibles.
- **`create-space`**: Crée un nouveau "space".
- **`get-space`**: Récupère les informations d'un "space" spécifique.
- **`update-space`**: Met à jour le nom ou la description d'un "space".

### 3. Gestion des Objets
- **`list-objects`**: Liste les objets au sein d'un "space" donné.
- **`create-object`**: Crée un nouvel objet (page, tâche, etc.) dans un "space".
- **`get-object`**: Récupère un objet spécifique par son ID.
- **`update-object`**: Met à jour les propriétés d'un objet existant (⚠️ ne permet pas de modifier le corps/contenu d'un objet existant — l'API l'accepte silencieusement sans l'appliquer ; il faut recréer un objet pour changer son contenu).
- **`delete-object`**: Archive (supprime) un objet.
- **`search-space`**: Recherche des objets à l'intérieur d'un "space" spécifique.

### 4. Gestion des "Lists" (Collections & Sets)
- **`add-list-objects`**: Ajoute des objets à une "list" (collection ou set).
- **`remove-list-object`**: Retire un objet d'une "list" (sans supprimer l'objet lui-même).
- **`get-list-views`**: Récupère les vues associées à une "list".
- **`get-list-objects`**: Récupère les objets contenus dans une "list".

### 5. Gestion des Membres
- **`list-members`**: Liste les membres d'un "space".
- **`get-member`**: Récupère les informations d'un membre spécifique.

### 6. Gestion des "Properties" (Propriétés)
- **`list-properties`**: Liste toutes les propriétés d'un "space".
- **`create-property`**: Crée une nouvelle propriété.
- **`get-property`**: Récupère une propriété spécifique.
- **`update-property`**: Met à jour une propriété existante.
- **`delete-property`**: Archive (supprime) une propriété.

### 7. Gestion des "Tags"
- **`list-tags`**: Liste les "tags" (options) pour une propriété de type "select" ou "multi-select".
- **`create-tag`**: Crée un nouveau "tag" pour une propriété.
- **`get-tag`**: Récupère un "tag" spécifique.
- **`update-tag`**: Met à jour un "tag" existant.
- **`delete-tag`**: Archive (supprime) un "tag".

### 8. Gestion des "Types" et "Templates"
- **`list-types`**: Liste tous les "types" d'objets disponibles dans un "space".
- **`create-type`**: Crée un nouveau "type" d'objet.
- **`get-type`**: Récupère la définition d'un "type" spécifique.
- **`update-type`**: Met à jour un "type" existant.
- **`delete-type`**: Archive (supprime) un "type".
- **`list-templates`**: Liste les "templates" (modèles) associés à un "type".
- **`get-template`**: Récupère un "template" spécifique.

### 9. Authentification
- **`create-auth-challenge`**: Déclenche l'affichage d'un code à 4 chiffres dans Anytype Desktop ; retourne un `challenge_id`. Nécessite une intervention humaine (lire le code affiché).
- **`create-api-key`**: Échange un `challenge_id` + le code à 4 chiffres contre une nouvelle clé API. Permet de générer une clé sans passer par l'UI des paramètres.

### 10. Gestion des Fichiers
- **`upload-file`**: Upload un fichier dans un "space" (contenu encodé en base64 côté appelant).
- **`download-file`**: Télécharge un fichier (contenu retourné encodé en base64).
- **`delete-file`**: Supprime un fichier (corbeille par défaut, `skip_bin: true` pour suppression définitive).

### 11. Gestion du Chat
- **`list-chats`**: Liste les "chats" d'un "space".
- **`create-chat`**: Crée un nouveau "chat".
- **`get-chat-messages`**: Liste les messages d'un chat.
- **`add-chat-message`**: Poste un nouveau message.
- **`get-chat-message`**: Récupère un message spécifique.
- **`edit-chat-message`**: Modifie le texte d'un message existant.
- **`delete-chat-message`**: Supprime un message.
- **`toggle-chat-reaction`**: Ajoute/retire une réaction emoji sur un message.
- **`read-chat-messages`**: Marque des messages comme lus.
- **`search-chat-messages`**: Recherche dans les messages d'un chat.
- **`read-chat-reactions`**: Marque des réactions comme lues.
- **`read-all-chat-messages`**: Marque tout le chat comme lu.
- **`chat-message-stream`**: ⚠️ Version **bornée** du flux SSE officiel — MCP fonctionne en requête/réponse, pas en abonnement persistant. Écoute pendant `timeout_seconds` (défaut 10s, max 60s) puis retourne les événements reçus durant cette fenêtre ; ce n'est pas un flux continu tant que l'outil n'est pas rappelé.

## Transports exposés

Le serveur écoute sur le port **1621** et expose le même jeu de 53 outils sur deux transports MCP en parallèle :

| Transport | Chemin | Utilisé par |
|---|---|---|
| SSE (legacy) | `http://<host>:1621/sse/` | Claude Code |
| Streamable HTTP | `http://<host>:1621/mcp/` | Codex, Antigravity |

Un endpoint `GET /` renvoie un simple statut JSON (`{"message": "..."}`) utile pour un healthcheck rapide.

## Configuration

Le serveur requiert les variables d'environnement suivantes :

- `ANYTYPE_API_URL` : URL de base de l'API locale d'Anytype. Par défaut, Anytype Desktop expose son API locale sur `http://127.0.0.1:31009` (le port **31009**, pas 27701 — vérifie avec `ss -ltnp | grep anytypeHelper` si besoin). Il faut que l'app Anytype soit ouverte sur la machine, et l'API locale activée dans ses paramètres (Réglages > Développeur/API locale), ce qui génère le token ci-dessous.
- `ANYTYPE_AUTH_TOKEN` : jeton Bearer généré dans Anytype. **Obligatoire, aucune valeur par défaut** — le serveur refuse de démarrer si absent.
- `ANYTYPE_VERSION` : version de l'API à cibler (ex: `2025-11-08`).

Pour le développement local (hors Docker), ces variables peuvent être définies via un fichier `.envrc` (chargé par `direnv`) ou exportées directement dans le shell.

**Le token n'a pas de fallback codé en dur** : c'est volontaire, pour éviter qu'une vieille clé de test ne traîne dans le code et ne soit utilisée par erreur.

## Installation et Lancement (avec Docker)

Ce projet est conçu pour être déployé sous forme de conteneur Docker, sur la **même machine** que l'application Anytype Desktop (le container doit atteindre son API locale).

1.  **Construire l'image** depuis la racine du projet :
    ```bash
    docker build -t mcp-anytype-server .
    ```

2.  **Réseau** : comme Anytype écoute sur `127.0.0.1` de la machine hôte, le container doit partager le réseau de l'hôte pour l'atteindre (sous Linux) :
    ```bash
    --network host
    ```
    (Le mapping `-p 1621:1621` est alors inutile/ignoré : le port 1621 du container devient directement celui de l'hôte.)

3.  **Démarrer le conteneur** — deux approches pour le token :

    *   **Rapide (variable d'environnement en clair)**, correct pour du test local :
        ```bash
        docker run -d --name anytype-mcp-server --network host \
          -e ANYTYPE_API_URL="http://localhost:31009" \
          -e ANYTYPE_AUTH_TOKEN="votre_token_secret" \
          -e ANYTYPE_VERSION="2025-11-08" \
          mcp-anytype-server
        ```
        ⚠️ Cette valeur reste visible en clair via `docker inspect` (et dans des outils comme Portainer) — à éviter dès que la clé n'est plus une clé de test jetable.

    *   **Recommandé (Docker secret monté en fichier)** — le token ne transite plus par les métadonnées du container :
        ```bash
        mkdir -p secrets && chmod 700 secrets
        # Écrire le token dans secrets/anytype_auth_token (chmod 600), en dehors de tout historique de commande partagé
        echo -n "votre_token_secret" > secrets/anytype_auth_token
        chmod 600 secrets/anytype_auth_token

        docker run -d --name anytype-mcp-server --network host \
          -v "$(pwd)/secrets/anytype_auth_token:/run/secrets/ANYTYPE_AUTH_TOKEN:ro" \
          -e ANYTYPE_API_URL="http://localhost:31009" \
          -e ANYTYPE_VERSION="2025-11-08" \
          mcp-anytype-server
        ```
        Le nom du fichier monté dans le container doit être **exactement** `ANYTYPE_AUTH_TOKEN` (majuscules) : c'est le chemin que `settings.py` regarde en priorité (`/run/secrets/ANYTYPE_AUTH_TOKEN`), avant de retomber sur la variable d'environnement du même nom si le fichier n'existe pas. Le dossier `secrets/` est exclu du build (`.dockerignore`) et ne part donc jamais dans l'image.

4.  **Vérifier que le conteneur tourne** :
    ```bash
    docker logs anytype-mcp-server
    curl http://localhost:1621/
    ```
    Vous devriez voir les messages de démarrage d'Uvicorn, puis un JSON `{"message": "Serveur MCP pour Anytype est en ligne avec 53 outils."}`.

## Intégration avec des clients MCP

Le serveur tourne une fois pour toutes (`http://localhost:1621`), et chaque client se déclare indépendamment. Rien à modifier côté serveur pour ajouter un nouveau client.

### Claude Code

Déclaration au niveau projet (`.mcp.json` à la racine du projet), ou via `claude mcp add` :
```json
{
  "mcpServers": {
    "anytype": {
      "type": "sse",
      "url": "http://localhost:1621/sse/"
    }
  }
}
```
(Le transport Streamable HTTP fonctionne aussi : `"type": "http", "url": "http://localhost:1621/mcp/"`.)

### Codex

Codex ne supporte, pour un serveur MCP distant en HTTP, que le transport **Streamable HTTP** (pas le SSE classique) — utiliser `/mcp/`, pas `/sse/`. Déclaration dans `~/.codex/config.toml` (globale) ou config projet équivalente :
```toml
[mcp_servers.anytype]
url = "http://localhost:1621/mcp/"

[mcp_servers.anytype.tools.list-spaces]
approval_mode = "approve"
# ... une entrée par outil si tu veux forcer l'approbation systématique
```

### Antigravity

Antigravity ne lit ni `.mcp.json`, ni un `mcp_config.json` posé à la racine du projet — il faut passer par un **plugin local**, scoppé au workspace, pour éviter d'activer le serveur globalement sur toutes les conversations. Le champ de déclaration s'appelle `serverUrl` (pas `url`).

⚠️ **Pointer vers `/mcp/` (Streamable HTTP), pas `/sse/`.** Le champ `serverUrl` a longtemps fonctionné en SSE, mais le client MCP d'Antigravity (CLI ≥ 1.2.10 en tout cas) négocie désormais en Streamable HTTP par défaut (`POST` direct) et ne retombe **pas** sur le SSE classique en cas d'échec — un `serverUrl` pointant sur `/sse/` produit une boucle de tentatives qui échouent en permanence (`405 Method Not Allowed`), sans jamais réussir à se connecter tant qu'on ne pointe pas sur `/mcp/`.

Arborescence à créer dans le projet cible :
```
.agents/
└── plugins/
    └── anytype/
        ├── plugin.json
        └── mcp_config.json
```

`.agents/plugins/anytype/plugin.json` :
```json
{
  "name": "anytype"
}
```

`.agents/plugins/anytype/mcp_config.json` :
```json
{
  "mcpServers": {
    "anytype": {
      "serverUrl": "http://127.0.0.1:1621/mcp/"
    }
  }
}
```

Dès que ce dossier est présent, le plugin est activé automatiquement pour ce workspace uniquement (redémarrer la session CLI pour que la découverte des outils ait lieu). Le fichier global `~/.gemini/config/mcp_config.json` existe aussi (il s'applique à *toutes* les conversations, tous projets confondus) — à éviter si tu veux garder une activation par projet.

## Évolutions futures

### Édition de contenu via l'API v2 (pas encore implémenté)

`update-object` ne permet pas de modifier le contenu (`body`) d'un objet existant — limitation confirmée de l'API v1 (le champ est accepté silencieusement mais jamais appliqué). Contournement actuel : recréer un objet plutôt que d'éditer l'existant.

Anytype expose en parallèle une **API v2** (pré-release, déjà active sur les instances à jour) qui permet une vraie édition de contenu via des opérations structurées, par ex. `PATCH /v2/spaces/{space_id}/objects/{object_id}` avec `{"ops":[{"op":"replace_text","find":"...","replace":"..."}]}`. Testé manuellement avec succès (remplacement de texte appliqué et persistant, relu ensuite via `get-object` v1).

Limites à connaître avant d'implémenter un outil dessus :
- C'est un **chercher/remplacer** précis (le texte à trouver doit matcher exactement une fois dans un bloc), pas un remplacement complet du contenu comme le `body` de `create-object`.
- **v2 est officiellement pré-release**, sans header `Anytype-Version` (donc pas de garantie de compatibilité dans le temps), et peut changer sans préavis selon la doc officielle d'Anyproto.
- Seules 2 opérations ont été confirmées disponibles à ce jour (`replace_text`, `add_property`) — la liste complète des opérations v2 n'a pas été explorée.
- Introduirait une dépendance mixte v1/v2 dans un serveur aujourd'hui entièrement v1.

À évaluer si le besoin d'éditer du contenu en place devient récurrent.
