from __future__ import annotations

from typing import Any

from backend.sentinel_audit import _load_kubernetes_config
from kubernetes import client


def build_hardening_plan() -> dict[str, Any]:
    _load_kubernetes_config()

    core_v1 = client.CoreV1Api()

    namespaces = core_v1.list_namespace().items
    services = core_v1.list_service_for_all_namespaces().items

    namespace_names = sorted(
        namespace.metadata.name
        for namespace in namespaces
    )

    namespace_items = []

    for namespace in namespace_names:
        namespace_items.append(
            {
                "namespace": namespace,
                "policies": [
                    "sentinel-default-deny",
                    "sentinel-core-infra",
                    "sentinel-infra-allow",
                ],
            }
        )

    workloads = []

    for service in services:
        selector = service.spec.selector or {}
        app = selector.get("app")

        if not app:
            continue

        ports = service.spec.ports or []
        port = ports[0].port if ports else 80

        workloads.append(
            {
                "app": app,
                "namespace": service.metadata.namespace,
                "port": port,
                "policy": (
                    f"sentinel-{app}-internal-bridge"
                ),
            }
        )

    groups = [
        {
            "id": "security-exceptions",
            "label": "Security stack exceptions",
            "description": (
                "Policies required by K-Guard, Wazuh and security tooling."
            ),
            "policies": [
                {
                    "name": "sentinel-exempt-stack",
                    "namespace": "k-guard",
                }
            ],
            "risk": "low",
        },
        {
            "id": "infra-allow",
            "label": "Infrastructure allow rules",
            "description": (
                "DNS, Kubernetes API and monitoring communication."
            ),
            "policies": [
                {
                    "name": "sentinel-infra-allow",
                    "namespace": namespace,
                }
                for namespace in namespace_names
            ],
            "risk": "medium",
        },
        {
            "id": "application-bridges",
            "label": "Application bridges",
            "description": (
                "Internal communication between discovered applications."
            ),
            "policies": [
                {
                    "name": item["policy"],
                    "namespace": item["namespace"],
                    "application": item["app"],
                    "port": item["port"],
                }
                for item in workloads
            ],
            "risk": "medium",
        },
        {
            "id": "external-access",
            "label": "External access exceptions",
            "description": (
                "Explicit egress rules for Webex and MongoDB Atlas."
            ),
            "policies": [
                {
                    "name": "sentinel-webex-egress",
                    "namespace": "k-guard",
                },
                {
                    "name": "sentinel-blog-db-access",
                    "namespace": "blog-prod",
                },
            ],
            "risk": "high",
        },
        {
            "id": "namespace-baseline",
            "label": "Namespace baseline",
            "description": (
                "Default deny and core isolation policies."
            ),
            "policies": [
                policy
                for item in namespace_items
                for policy in (
                    {
                        "name": "sentinel-default-deny",
                        "namespace": item["namespace"],
                    },
                    {
                        "name": "sentinel-core-infra",
                        "namespace": item["namespace"],
                    },
                )
            ],
            "risk": "critical",
        },
    ]

    for group in groups:
        group["count"] = len(group["policies"])

    return {
        "groups": groups,
        "total_policies": sum(
            group["count"]
            for group in groups
        ),
        "namespaces": namespace_names,
        "workloads": workloads,
        "ordering": [
            "security-exceptions",
            "infra-allow",
            "application-bridges",
            "external-access",
            "namespace-baseline",
        ],
        "read_only": True,
    }
