import os
import httpx

from typing import Any
from pathlib import Path



class WazuhIndexerClientError(Exception):
    """Raised when Wazuh Indexer cannot be queried safely."""


class WazuhIndexerClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("WAZUH_INDEXER_URL", "").rstrip("/")
        self.ca_file = os.getenv("WAZUH_INDEXER_CA_FILE", "/etc/kguard/wazuh-indexer-ca/root-ca.pem")
        self.cert_file = "/etc/kguard/wazuh-indexer-client/admin.pem"
        self.key_file = "/etc/kguard/wazuh-indexer-client/admin-key.pem"

        if not self.base_url:
            raise RuntimeError("WAZUH_INDEXER_URL is missing")

        for path in (self.ca_file, self.cert_file, self.key_file):
            if not Path(path).is_file():
                raise RuntimeError(f"Wazuh Indexer TLS file is missing: {path}")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            cert=(self.cert_file, self.key_file),
            verify=False,
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=False,
        )

    async def _search(self, index: str, query: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self._client() as client:
                response = await client.post(
                    f"/{index}/_search",
                    json=query,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as error:
            raise WazuhIndexerClientError(
                f"Wazuh Indexer request failed for {index}"
            ) from error
        except ValueError as error:
            raise WazuhIndexerClientError(
                "Wazuh Indexer returned invalid JSON"
            ) from error

    @staticmethod
    def _total(payload: dict[str, Any]) -> int:
        total = (payload.get("hits") or {}).get("total", 0)
        return int(total.get("value", 0)) if isinstance(total, dict) else int(total or 0)

    @staticmethod
    def _normalize_alert(hit: dict[str, Any]) -> dict[str, Any]:
        source = hit.get("_source") or {}
        agent = source.get("agent") or {}
        manager = source.get("manager") or {}
        rule = source.get("rule") or {}
        mitre = rule.get("mitre") or {}

        return {
            "id": hit.get("_id", ""),
            "timestamp": source.get("@timestamp") or source.get("timestamp") or "",
            "level": int(rule.get("level") or 0),
            "rule_id": str(rule.get("id") or ""),
            "description": rule.get("description") or "Wazuh alert",
            "firedtimes": int(rule.get("firedtimes") or 0),
            "groups": rule.get("groups") or [],
            "agent": {
                "id": str(agent.get("id") or ""),
                "name": agent.get("name") or "Unknown",
                "ip": agent.get("ip") or "N/A",
            },
            "manager": {
                "name": manager.get("name") or "N/A",
            },
            "mitre": {
                "ids": mitre.get("id") or [],
                "techniques": mitre.get("technique") or [],
                "tactics": mitre.get("tactic") or [],
            },
            "location": source.get("location") or "N/A",
            "decoder": source.get("decoder") or {},
            "predecoder": source.get("predecoder") or {},
            "data": source.get("data") or {},
            "syscheck": (
                source.get("syscheck")
                or (source.get("data") or {}).get("syscheck")
                or {}
            ),
            "full_log": source.get("full_log") or "",
        }

    async def get_alerts(self, limit: int = 50) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 100))
        payload = await self._search(
            "wazuh-alerts-*",
            {
                "size": safe_limit,
                "track_total_hits": True,
                "sort": [{"@timestamp": {"order": "desc"}}],
                "_source": [
                    "@timestamp",
                    "timestamp",
                    "agent.id",
                    "agent.name",
                    "agent.ip",
                    "rule.id",
                    "rule.level",
                    "rule.description",
                    "rule.firedtimes",
                    "rule.groups",
                    "rule.mitre",
                    "agent.id",
                    "agent.name",
                    "agent.ip",
                    "manager.name",
                    "decoder",
                    "predecoder",
                    "data",
                    "syscheck",
                    "location",
                    "full_log",
                ],
            },
        )
        return {
            "available": True,
            "total": self._total(payload),
            "alerts": [self._normalize_alert(hit) for hit in (payload.get("hits") or {}).get("hits", [])],
        }

    async def get_alert_summary(self) -> dict[str, int]:
        payload = await self._search(
            "wazuh-alerts-*",
            {
                "size": 0,
                "track_total_hits": True,
                "aggs": {
                    "by_level": {
                        "terms": {
                            "field": "rule.level",
                            "size": 20,
                        }
                    }
                },
            },
        )

        buckets = (((payload.get("aggregations") or {}).get("by_level") or {}).get("buckets") or [])
        by_level = {int(bucket.get("key")): int(bucket.get("doc_count", 0)) for bucket in buckets}

        return {
            "total": self._total(payload),
            "critical": sum(count for level, count in by_level.items() if level >= 15),
            "high": sum(count for level, count in by_level.items() if 12 <= level <= 14),
            "medium": sum(count for level, count in by_level.items() if 7 <= level <= 11),
            "low": sum(count for level, count in by_level.items() if level <= 6),
        }


wazuh_indexer_client = WazuhIndexerClient()