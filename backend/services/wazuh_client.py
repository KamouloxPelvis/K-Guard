import asyncio
import os
import time
from typing import Any

import httpx


class WazuhClientError(Exception):
    """Raised when the Wazuh API cannot be reached or returns an invalid response."""


class WazuhClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("WAZUH_API_URL", "").rstrip("/")
        self.username = os.getenv("WAZUH_API_USERNAME", "")
        self.password = os.getenv("WAZUH_API_PASSWORD", "")
        self.ca_file = os.getenv("WAZUH_API_CA_FILE", "")
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

        if not all([self.base_url, self.username, self.password, self.ca_file]):
            raise RuntimeError("Wazuh API environment configuration is incomplete")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            verify=False,
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=False,
        )

    async def _authenticate(self) -> str:
        async with self._token_lock:
            if self._token and time.time() < self._token_expires_at:
                return self._token

            try:
                async with self._client() as client:
                    response = await client.get(
                        "/security/user/authenticate",
                        params={"raw": "true"},
                        auth=(self.username, self.password),
                    )
                    response.raise_for_status()
            except httpx.HTTPError as error:
                raise WazuhClientError("Unable to authenticate with Wazuh API") from error

            token = response.text.strip()
            if not token:
                raise WazuhClientError("Wazuh API returned an empty authentication token")

            self._token = token
            self._token_expires_at = time.time() + 540
            return token

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token = await self._authenticate()

        try:
            async with self._client() as client:
                response = await client.get(
                    path,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 401:
                    self._token = None
                    self._token_expires_at = 0.0
                    token = await self._authenticate()
                    response = await client.get(
                        path,
                        params=params,
                        headers={"Authorization": f"Bearer {token}"},
                    )

                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as error:
            raise WazuhClientError(f"Wazuh API request failed for {path}") from error
        except ValueError as error:
            raise WazuhClientError("Wazuh API returned invalid JSON") from error

    @staticmethod
    def _normalize_agent(agent: dict[str, Any]) -> dict[str, Any]:
        os_data = agent.get("os") or {}

        return {
            "id": str(agent.get("id", "")),
            "name": agent.get("name", "Unknown"),
            "status": agent.get("status", "unknown"),
            "ip": agent.get("ip", "N/A"),
            "group": ", ".join(agent.get("group") or []) or "default",
            "version": agent.get("version", "N/A"),
            "last_keep_alive": agent.get("lastKeepAlive", "Never"),
            "os": {
                "name": os_data.get("name", "Unknown"),
                "platform": os_data.get("platform", "Unknown"),
                "version": os_data.get("version", "Unknown"),
                "architecture": os_data.get("arch", "Unknown"),
            },
        }

    async def get_agents(self) -> dict[str, Any]:
        payload = await self._get(
            "/agents",
            {
                "limit": 500,
                "select": (
                    "id,name,status,ip,group,version,lastKeepAlive,"
                    "os.name,os.platform,os.version,os.arch"
                ),
            },
        )

        data = payload.get("data") or {}
        agents = [
            self._normalize_agent(agent)
            for agent in data.get("affected_items", [])
            if str(agent.get("id", "")) != "000"
        ]

        summary = {
            "total": len(agents),
            "active": sum(agent["status"] == "active" for agent in agents),
            "disconnected": sum(agent["status"] == "disconnected" for agent in agents),
            "never_connected": sum(
                agent["status"] == "never_connected" for agent in agents
            ),
        }

        return {
            "connected": True,
            "summary": summary,
            "agents": agents,
        }


wazuh_client = WazuhClient()