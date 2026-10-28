import asyncio
import base64
import json
import httpx
from typing import Optional, Dict, Any, List, Union

# Ajout du chemin pour importer les settings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import settings


class AnytypeClient:
    """
    Client pour interagir avec l'API REST d'Anytype, basé sur le schéma fourni.
    """
    def __init__(self):
        self.api_url = settings.anytype_api_url
        self.headers = {
            "Authorization": f"Bearer {settings.anytype_auth_token}",
            "Anytype-Version": settings.anytype_version,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.api_url.rstrip('/')}{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                # Gérer les réponses vides (204 No Content, ou 200 avec un corps vide)
                if response.status_code == 204 or not response.content:
                    return {"success": True}
                data = response.json()
                # Certains endpoints (ex: add-list-objects) renvoient une simple chaîne JSON
                # au lieu d'un objet ; on la normalise pour respecter le type de retour Dict.
                if not isinstance(data, dict):
                    return {"result": data}
                return data
            except httpx.HTTPStatusError as e:
                return {"error": str(e), "response_text": e.response.text}
            except httpx.RequestError as e:
                return {"error": str(e)}

    async def _call_tool_endpoint(self, tool_name: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode générique pour appeler un endpoint basé sur le nom de l'outil."""
        # Nettoyage des paramètres non envoyés ('self' fuite de locals() dans les méthodes d'instance ;
        # 'compact' est géré côté client après coup, jamais transmis à l'API Anytype)
        request_params = {k: v for k, v in params.items() if v is not None and k not in ('self', 'compact')}

        # Logique de mapping de nom d'outil à endpoint
        # Ceci est une heuristique et pourrait nécessiter des ajustements
        resource_map = {
            "create-auth-challenge": "/v1/auth/challenges",
            "create-api-key": "/v1/auth/api_keys",
            "delete-file": f"/v1/spaces/{params.get('space_id')}/files/{params.get('file_id')}",
            "list-chats": f"/v1/spaces/{params.get('space_id')}/chats",
            "create-chat": f"/v1/spaces/{params.get('space_id')}/chats",
            "get-chat-messages": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages",
            "add-chat-message": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages",
            "get-chat-message": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages/{params.get('message_id')}",
            "edit-chat-message": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages/{params.get('message_id')}",
            "delete-chat-message": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages/{params.get('message_id')}",
            "toggle-chat-reaction": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages/{params.get('message_id')}/reactions",
            "read-chat-messages": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages/read",
            "search-chat-messages": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/messages/search",
            "read-chat-reactions": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/reactions/read",
            "read-all-chat-messages": f"/v1/spaces/{params.get('space_id')}/chats/{params.get('chat_id')}/read_all",
            "search-global": "/v1/search",
            "list-spaces": "/v1/spaces",
            "create-space": "/v1/spaces",
            "get-space": f"/v1/spaces/{params.get('space_id')}",
            "update-space": f"/v1/spaces/{params.get('space_id')}",
            "add-list-objects": f"/v1/spaces/{params.get('space_id')}/lists/{params.get('list_id')}/objects",
            "remove-list-object": f"/v1/spaces/{params.get('space_id')}/lists/{params.get('list_id')}/objects/{params.get('object_id')}",
            "get-list-views": f"/v1/spaces/{params.get('space_id')}/lists/{params.get('list_id')}/views",
            "get-list-objects": f"/v1/spaces/{params.get('space_id')}/lists/{params.get('list_id')}/objects",
            "list-members": f"/v1/spaces/{params.get('space_id')}/members",
            "get-member": f"/v1/spaces/{params.get('space_id')}/members/{params.get('member_id')}",
            "list-objects": f"/v1/spaces/{params.get('space_id')}/objects",
            "create-object": f"/v1/spaces/{params.get('space_id')}/objects",
            "get-object": f"/v1/spaces/{params.get('space_id')}/objects/{params.get('object_id')}",
            "update-object": f"/v1/spaces/{params.get('space_id')}/objects/{params.get('object_id')}",
            "delete-object": f"/v1/spaces/{params.get('space_id')}/objects/{params.get('object_id')}",
            "list-properties": f"/v1/spaces/{params.get('space_id')}/properties",
            "create-property": f"/v1/spaces/{params.get('space_id')}/properties",
            "get-property": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}",
            "update-property": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}",
            "delete-property": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}",
            "list-tags": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}/tags",
            "create-tag": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}/tags",
            "get-tag": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}/tags/{params.get('tag_id')}",
            "update-tag": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}/tags/{params.get('tag_id')}",
            "delete-tag": f"/v1/spaces/{params.get('space_id')}/properties/{params.get('property_id')}/tags/{params.get('tag_id')}",
            "search-space": f"/v1/spaces/{params.get('space_id')}/search",
            "list-types": f"/v1/spaces/{params.get('space_id')}/types",
            "create-type": f"/v1/spaces/{params.get('space_id')}/types",
            "get-type": f"/v1/spaces/{params.get('space_id')}/types/{params.get('type_id')}",
            "update-type": f"/v1/spaces/{params.get('space_id')}/types/{params.get('type_id')}",
            "delete-type": f"/v1/spaces/{params.get('space_id')}/types/{params.get('type_id')}",
            "list-templates": f"/v1/spaces/{params.get('space_id')}/types/{params.get('type_id')}/templates",
            "get-template": f"/v1/spaces/{params.get('space_id')}/types/{params.get('type_id')}/templates/{params.get('template_id')}",
        }

        endpoint = resource_map.get(tool_name)

        # Les IDs déjà présents dans le chemin ne doivent pas être répétés dans l'URL ou le corps
        path_ids = ['space_id', 'list_id', 'member_id', 'object_id', 'property_id', 'tag_id', 'type_id', 'template_id', 'file_id', 'chat_id', 'message_id']
        remaining_params = {k: v for k, v in request_params.items() if k not in path_ids}

        if method in ("GET", "DELETE"):
            return await self._request(method, endpoint, params=remaining_params)

        # search-global/search-space sont en POST mais l'API attend offset/limit en query string,
        # pas dans le corps JSON (vérifié empiriquement : ignorés silencieusement sinon).
        if tool_name in ("search-global", "search-space"):
            query_params = {k: v for k, v in remaining_params.items() if k in ("offset", "limit")}
            body_params = {k: v for k, v in remaining_params.items() if k not in ("offset", "limit")}
            return await self._request(method, endpoint, params=query_params, json=body_params)

        return await self._request(method, endpoint, json=remaining_params)

    @staticmethod
    def _compact_object(obj: Dict[str, Any], include_markdown: bool = False) -> Dict[str, Any]:
        """Réduit un objet Anytype à ses champs essentiels (id, nom, type, space, date),
        pour éviter de réembarquer l'intégralité du schéma de type à chaque élément d'une liste."""
        last_modified = None
        for prop in obj.get("properties", []) or []:
            if prop.get("key") == "last_modified_date":
                last_modified = prop.get("date")
                break
        compact = {
            "id": obj.get("id"),
            "name": obj.get("name"),
            "type": (obj.get("type") or {}).get("key"),
            "space_id": obj.get("space_id"),
            "last_modified_date": last_modified,
        }
        if include_markdown:
            compact["markdown"] = obj.get("markdown")
        return compact

    # --- Implémentation de chaque outil ---

    async def create_auth_challenge(self, app_name: str) -> Dict[str, Any]:
        """
        Déclenche l'affichage d'un code à 4 chiffres dans Anytype Desktop.
        Retourne un challenge_id à réutiliser avec create_api_key une fois le code lu par l'utilisateur.
        """
        return await self._call_tool_endpoint("create-auth-challenge", "POST", locals())

    async def create_api_key(self, challenge_id: str, code: str) -> Dict[str, Any]:
        """
        Échange un challenge_id + le code à 4 chiffres (affiché dans Anytype Desktop) contre une nouvelle clé API.
        """
        return await self._call_tool_endpoint("create-api-key", "POST", locals())

    async def search_global(self, query: Optional[str] = None, offset: int = 0, limit: int = 100, sort: Optional[Dict] = None, types: Optional[List[str]] = None, compact: Optional[bool] = False) -> Dict[str, Any]:
        results = await self._call_tool_endpoint("search-global", "POST", locals())
        # Ajout de l'ID composite (space_id/object_id) pour que 'fetch' puisse retrouver l'objet
        if "data" in results and isinstance(results["data"], list):
            for item in results["data"]:
                if "id" in item and "space_id" in item:
                    item["id"] = f"{item['space_id']}/{item['id']}"
            if compact:
                results["data"] = [self._compact_object(o) for o in results["data"]]
        return results

    async def list_spaces(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-spaces", "GET", locals())

    async def create_space(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("create-space", "POST", locals())

    async def get_space(self, space_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-space", "GET", locals())

    async def update_space(self, space_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("update-space", "PATCH", locals())

    async def add_list_objects(self, space_id: str, list_id: str, objects: Optional[List[str]] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("add-list-objects", "POST", locals())

    async def remove_list_object(self, space_id: str, list_id: str, object_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("remove-list-object", "DELETE", locals())

    async def get_list_views(self, space_id: str, list_id: str, offset: int = 0, limit: Optional[int] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-list-views", "GET", locals())

    async def get_list_objects(self, space_id: str, list_id: str, view_id: str, offset: int = 0, limit: Optional[int] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-list-objects", "GET", locals())

    async def list_members(self, space_id: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-members", "GET", locals())

    async def get_member(self, space_id: str, member_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-member", "GET", locals())

    async def list_objects(self, space_id: str, offset: int = 0, limit: int = 100, compact: Optional[bool] = False) -> Dict[str, Any]:
        results = await self._call_tool_endpoint("list-objects", "GET", locals())
        if compact and isinstance(results.get("data"), list):
            results["data"] = [self._compact_object(o) for o in results["data"]]
        return results

    async def create_object(self, space_id: str, type_key: str, body: Optional[str] = None, icon: Optional[Dict] = None, name: Optional[str] = None, properties: Optional[List[Dict]] = None, template_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("create-object", "POST", locals())

    async def get_object(self, space_id: str, object_id: str, format: str = "md", compact: Optional[bool] = False) -> Dict[str, Any]:
        results = await self._call_tool_endpoint("get-object", "GET", locals())
        if compact and isinstance(results.get("object"), dict):
            results["object"] = self._compact_object(results["object"], include_markdown=True)
        return results

    async def update_object(self, space_id: str, object_id: str, icon: Optional[Dict] = None, name: Optional[str] = None, properties: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("update-object", "PATCH", locals())

    async def delete_object(self, space_id: str, object_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("delete-object", "DELETE", locals())

    async def list_properties(self, space_id: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-properties", "GET", locals())

    async def create_property(self, space_id: str, format: str, name: str, key: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("create-property", "POST", locals())

    async def get_property(self, space_id: str, property_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-property", "GET", locals())

    async def update_property(self, space_id: str, property_id: str, name: str, key: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("update-property", "PATCH", locals())

    async def delete_property(self, space_id: str, property_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("delete-property", "DELETE", locals())

    async def list_tags(self, space_id: str, property_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-tags", "GET", locals())

    async def create_tag(self, space_id: str, property_id: str, color: str, name: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("create-tag", "POST", locals())

    async def get_tag(self, space_id: str, property_id: str, tag_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-tag", "GET", locals())

    async def update_tag(self, space_id: str, property_id: str, tag_id: str, color: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("update-tag", "PATCH", locals())

    async def delete_tag(self, space_id: str, property_id: str, tag_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("delete-tag", "DELETE", locals())

    async def search_space(self, space_id: str, query: Optional[str] = None, offset: int = 0, limit: int = 100, sort: Optional[Dict] = None, types: Optional[List[str]] = None, compact: Optional[bool] = False) -> Dict[str, Any]:
        results = await self._call_tool_endpoint("search-space", "POST", locals())
        if compact and isinstance(results.get("data"), list):
            results["data"] = [self._compact_object(o) for o in results["data"]]
        return results

    async def list_types(self, space_id: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-types", "GET", locals())

    async def create_type(self, space_id: str, layout: str, name: str, plural_name: str, icon: Optional[Dict] = None, key: Optional[str] = None, properties: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("create-type", "POST", locals())

    async def get_type(self, space_id: str, type_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-type", "GET", locals())

    async def update_type(self, space_id: str, type_id: str, icon: Optional[Dict] = None, key: Optional[str] = None, layout: Optional[str] = None, name: Optional[str] = None, plural_name: Optional[str] = None, properties: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("update-type", "PATCH", locals())

    async def delete_type(self, space_id: str, type_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("delete-type", "DELETE", locals())

    async def list_templates(self, space_id: str, type_id: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-templates", "GET", locals())

    async def get_template(self, space_id: str, type_id: str, template_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-template", "GET", locals())

    async def upload_file(self, space_id: str, filename: str, content_base64: str) -> Dict[str, Any]:
        """
        Upload un fichier dans un space. Le contenu doit être encodé en base64 (paramètre content_base64).
        """
        try:
            file_bytes = base64.b64decode(content_base64)
        except Exception as e:
            return {"error": f"Invalid base64 content: {e}"}

        url = f"{self.api_url.rstrip('/')}/v1/spaces/{space_id}/files"
        headers = {k: v for k, v in self.headers.items() if k.lower() != "content-type"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, files={"file": (filename, file_bytes)})
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {"error": str(e), "response_text": e.response.text}
            except httpx.RequestError as e:
                return {"error": str(e)}

    async def download_file(self, space_id: str, file_id: str, width: Optional[int] = None) -> Dict[str, Any]:
        """
        Télécharge un fichier. Le contenu est retourné encodé en base64 (champ content_base64).
        """
        url = f"{self.api_url.rstrip('/')}/v1/spaces/{space_id}/files/{file_id}"
        params = {"width": width} if width is not None else {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return {
                    "content_type": response.headers.get("content-type", "application/octet-stream"),
                    "size": len(response.content),
                    "content_base64": base64.b64encode(response.content).decode("ascii"),
                }
            except httpx.HTTPStatusError as e:
                return {"error": str(e), "response_text": e.response.text}
            except httpx.RequestError as e:
                return {"error": str(e)}

    async def delete_file(self, space_id: str, file_id: str, skip_bin: Optional[bool] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("delete-file", "DELETE", locals())

    async def list_chats(self, space_id: str, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("list-chats", "GET", locals())

    async def create_chat(self, space_id: str, name: str, icon: Optional[Dict] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("create-chat", "POST", locals())

    async def get_chat_messages(self, space_id: str, chat_id: str, before_order_id: Optional[str] = None, after_order_id: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-chat-messages", "GET", locals())

    async def add_chat_message(self, space_id: str, chat_id: str, text: str, style: Optional[str] = None, marks: Optional[List[Dict]] = None, attachments: Optional[List[Dict]] = None, reply_to_message_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("add-chat-message", "POST", locals())

    async def get_chat_message(self, space_id: str, chat_id: str, message_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("get-chat-message", "GET", locals())

    async def edit_chat_message(self, space_id: str, chat_id: str, message_id: str, text: str, style: Optional[str] = None, marks: Optional[List[Dict]] = None, attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("edit-chat-message", "PATCH", locals())

    async def delete_chat_message(self, space_id: str, chat_id: str, message_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("delete-chat-message", "DELETE", locals())

    async def toggle_chat_reaction(self, space_id: str, chat_id: str, message_id: str, emoji: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("toggle-chat-reaction", "POST", locals())

    async def read_chat_messages(self, space_id: str, chat_id: str, type: Optional[str] = None, after_order_id: Optional[str] = None, before_order_id: Optional[str] = None, last_state_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("read-chat-messages", "POST", locals())

    async def search_chat_messages(self, space_id: str, chat_id: str, query: Optional[str] = None, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._call_tool_endpoint("search-chat-messages", "GET", locals())

    async def read_chat_reactions(self, space_id: str, chat_id: str, order_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._call_tool_endpoint("read-chat-reactions", "POST", locals())

    async def read_all_chat_messages(self, space_id: str, chat_id: str) -> Dict[str, Any]:
        return await self._call_tool_endpoint("read-all-chat-messages", "POST", locals())

    async def chat_message_stream(self, space_id: str, chat_id: str, timeout_seconds: float = 10.0, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Écoute le flux SSE de nouveaux messages de chat pendant une durée bornée (défaut 10s, max 60s)
        et retourne les événements reçus durant cette fenêtre. Ce n'est PAS un abonnement persistant :
        chaque appel ouvre puis referme sa propre connexion (adapté au modèle requête/réponse de MCP).
        """
        timeout_seconds = min(max(timeout_seconds, 1.0), 60.0)
        url = f"{self.api_url.rstrip('/')}/v1/spaces/{space_id}/chats/{chat_id}/messages/stream"
        params = {"limit": limit} if limit is not None else {}
        events: List[Any] = []

        async def _collect():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url, headers=self.headers, params=params) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            raw = line[len("data:"):].strip()
                            if raw:
                                try:
                                    events.append(json.loads(raw))
                                except json.JSONDecodeError:
                                    events.append({"raw": raw})

        try:
            await asyncio.wait_for(_collect(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            pass
        except httpx.HTTPStatusError as e:
            return {"error": str(e), "response_text": e.response.text}
        except httpx.RequestError as e:
            return {"error": str(e)}

        return {"events": events, "listened_seconds": timeout_seconds}

    async def fetch(self, composite_id: str) -> Dict[str, Any]:
        """
        Retrieve the full content of a search result document using its composite ID (e.g., 'space_id/object_id').
        """
        try:
            space_id, object_id = composite_id.split('/', 1)
        except ValueError:
            return {"error": "Invalid ID format. Expected 'space_id/object_id'."}

        return await self.get_object(space_id, object_id)

# Instance unique du client
anytype_client = AnytypeClient()
