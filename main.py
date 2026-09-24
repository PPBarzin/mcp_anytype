from fastapi import FastAPI
from mcp.server.fastmcp.tools.base import Tool
from mcp.server.fastmcp.server import FastMCP
from typing import Dict, Any, Optional, List
import json
import os
import inspect
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from anytype_client import anytype_client

# --- Création de la liste d'outils à partir du client et du JSON ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

tools = []
client_methods = inspect.getmembers(anytype_client, predicate=inspect.iscoroutinefunction)

# Charger les métadonnées des outils depuis le fichier JSON externe
try:
    with open(os.path.join(BASE_DIR, 'tools.json'), 'r', encoding='utf-8') as f:
        tools_metadata = json.load(f)
    tools_map = {t['name']: t['description'] for t in tools_metadata['tools']}
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading or parsing tools.json: {e}")
    # En cas d'erreur, on continue avec des descriptions basiques
    tools_map = {}

for method_name, method_coro in client_methods:
    if method_name.startswith('_') or method_name == 'fetch':
        continue

    tool_name_kebab = method_name.replace('_', '-')

    # Utiliser la description du JSON si disponible, sinon le docstring
    description = tools_map.get(tool_name_kebab, method_coro.__doc__ or "No description available.")

    # Pour RAGFlow, l'outil de recherche principal doit s'appeler 'search'
    if method_name == "search_global":
        tools.append(Tool.from_function(fn=method_coro, name="search", description=description))
    else:
        # Les autres outils gardent leur nom API
        tools.append(Tool.from_function(fn=method_coro, name=tool_name_kebab, description=description))

# Ajout de l'outil 'fetch' qui est essentiel pour RAGFlow
fetch_description = "Retrieve the full content of a search result document using its composite ID (e.g., 'space_id/object_id')."
tools.append(
    Tool.from_function(
        fn=anytype_client.fetch,
        name="fetch",
        description=fetch_description
    )
)

# --- Création du serveur ---

mcp_server = FastMCP(
    tools=tools,
    sse_path="/",
    streamable_http_path="/",
)

app = FastAPI(
    title="Serveur MCP pour Anytype",
    version="2.1.0", # Version incrémentée
    description="Un serveur MCP pour connecter RAGFlow à Anytype, basé sur le schéma d'API officiel chargé depuis tools.json.",
    lifespan=lambda _app: mcp_server.session_manager.run(),
)

# Transport SSE (legacy) : utilisé par ex. par Antigravity/Gemini
app.mount("/sse", mcp_server.sse_app())

# Transport Streamable HTTP : requis par ex. par Codex
app.mount("/mcp", mcp_server.streamable_http_app())

@app.get("/")
def read_root():
    return {"message": f"Serveur MCP pour Anytype est en ligne avec {len(tools)} outils."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(host="0.0.0.0", port=1621, reload=True, app="main:app")
