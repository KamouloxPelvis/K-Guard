from __future__ import annotations

import json
import os
from types import SimpleNamespace
from datetime import datetime, timezone
from typing import Any

from kubernetes import client, config



def _load_kubernetes_config() -> None:
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


CATEGORY_WEIGHTS = {
    "network_policies": 30,
    "pod_hardening": 35,
    "exposure": 15,
    "admission": 10,
    "supply_chain": 10,
}

SYSTEM_NAMESPACES = {
    item.strip()
    for item in os.getenv(
        "SENTINEL_SYSTEM_NAMESPACES",
        "kube-system,kube-public,kube-node-lease",
    ).split(",")
    if item.strip()
}


def _finding(
    findings: list[dict[str, Any]],
    finding_id: str,
    severity: str,
    message: str,
    namespace: str | None = None,
    resource: str | None = None,
) -> None:
    findings.append(
        {
            "id": finding_id,
            "severity": severity,
            "message": message,
            "namespace": namespace,
            "resource": resource,
        }
    )


def _category_result(
    checks: list[dict[str, Any]],
    weight: int,
) -> dict[str, Any]:
    passed = sum(check["status"] == "passed" for check in checks)
    failed = sum(check["status"] == "failed" for check in checks)
    unknown = sum(check["status"] == "unknown" for check in checks)
    total = len(checks)
    evaluated = passed + failed

    # Unknown ne constitue jamais une réussite.
    # Il réduit le score et la couverture, sans être assimilé à un échec certain.
    score = round((passed / total) * 100) if total else None

    return {
        "score": score,
        "weight": weight,
        "passed": passed,
        "failed": failed,
        "unknown": unknown,
        "total": total,
        "evaluated": evaluated,
    }


def _match_network_policy(
    policy: Any,
    pod: Any,
) -> bool:
    selector = policy.spec.pod_selector

    if not selector:
        return True

    pod_labels = pod.metadata.labels or {}
    match_labels = selector.match_labels or {}

    if any(pod_labels.get(key) != value for key, value in match_labels.items()):
        return False

    for expression in selector.match_expressions or []:
        key = expression.key
        operator = expression.operator
        values = expression.values or []
        present = key in pod_labels

        if operator == "Exists" and not present:
            return False
        if operator == "DoesNotExist" and present:
            return False
        if operator == "In" and pod_labels.get(key) not in values:
            return False
        if operator == "NotIn" and pod_labels.get(key) in values:
            return False

    return True


def _audit_network(
    namespaces: list[Any],
    pods_by_namespace: dict[str, list[Any]],
    policies_by_namespace: dict[str, list[Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    for namespace in namespaces:
        name = namespace.metadata.name
        active_pods = [
            pod
            for pod in pods_by_namespace.get(name, [])
            if pod.status.phase not in {"Succeeded", "Failed"}
        ]

        if not active_pods:
            continue

        policies = policies_by_namespace.get(name, [])

        if not policies:
            checks.append({"status": "failed"})
            _finding(
                findings,
                "network-policy-missing",
                "critical",
                "No NetworkPolicy applies to workloads in this namespace.",
                name,
            )
            continue

        covered = sum(
            any(_match_network_policy(policy, pod) for policy in policies)
            for pod in active_pods
        )

        if covered == len(active_pods):
            checks.append({"status": "passed"})
        else:
            checks.append({"status": "failed"})
            _finding(
                findings,
                "network-policy-incomplete",
                "high",
                f"{len(active_pods) - covered} active workload(s) are not selected by any NetworkPolicy.",
                name,
            )

    return checks


def _audit_pods(
    pods: list[Any],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    for pod in pods:
        if pod.status.phase in {"Succeeded", "Failed"}:
            _finding(
                findings,
                "completed-privileged-pod",
                "medium",
                "Completed Pod retained in the cluster inventory.",
                pod.metadata.namespace,
                pod.metadata.name,
            )
            continue

        namespace = pod.metadata.namespace
        name = pod.metadata.name
        pod_spec = pod.spec

        for field, value, finding_id, message in (
            (
                "host_network",
                pod_spec.host_network,
                "pod-host-network",
                "Workload uses hostNetwork.",
            ),
            (
                "host_pid",
                pod_spec.host_pid,
                "pod-host-pid",
                "Workload uses hostPID.",
            ),
            (
                "host_ipc",
                pod_spec.host_ipc,
                "pod-host-ipc",
                "Workload uses hostIPC.",
            ),
        ):
            if value is True:
                checks.append({"status": "failed"})
                _finding(findings, finding_id, "high", message, namespace, name)
            else:
                checks.append({"status": "passed"})

        containers = list(pod_spec.containers or []) + list(
            pod_spec.init_containers or []
        )

        for container in containers:
            security = container.security_context

            if security is None:
                checks.append({"status": "unknown"})
                _finding(
                    findings,
                    "container-security-context-missing",
                    "medium",
                    f"Container {container.name} has no explicit securityContext.",
                    namespace,
                    name,
                )
            else:
                if security.privileged is True:
                    checks.append({"status": "failed"})
                    _finding(
                        findings,
                        "container-privileged",
                        "critical",
                        f"Container {container.name} runs privileged.",
                        namespace,
                        name,
                    )
                else:
                    checks.append({"status": "passed"})

                if security.allow_privilege_escalation is True:
                    checks.append({"status": "failed"})
                    _finding(
                        findings,
                        "privilege-escalation-enabled",
                        "high",
                        f"Container {container.name} allows privilege escalation.",
                        namespace,
                        name,
                    )
                elif security.allow_privilege_escalation is False:
                    checks.append({"status": "passed"})
                else:
                    checks.append({"status": "unknown"})

                if security.run_as_non_root is True:
                    checks.append({"status": "passed"})
                elif security.run_as_non_root is False:
                    checks.append({"status": "failed"})
                    _finding(
                        findings,
                        "run-as-root-allowed",
                        "high",
                        f"Container {container.name} does not enforce runAsNonRoot.",
                        namespace,
                        name,
                    )
                else:
                    checks.append({"status": "unknown"})

                if security.read_only_root_filesystem is True:
                    checks.append({"status": "passed"})
                else:
                    checks.append({"status": "unknown"})

            image = container.image or ""

            if image.endswith(":latest"):
                checks.append({"status": "failed"})
                _finding(
                    findings,
                    "mutable-image-tag",
                    "medium",
                    f"Container {container.name} uses the mutable latest tag.",
                    namespace,
                    name,
                )
            elif "@sha256:" in image:
                checks.append({"status": "passed"})
            else:
                checks.append({"status": "unknown"})

    return checks


def _audit_exposure(
    services: list[Any],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    for service in services:
        service_type = service.spec.type

        if service_type in {"NodePort", "LoadBalancer"}:
            checks.append({"status": "failed"})
            _finding(
                findings,
                "service-exposed",
                "medium",
                f"Service type {service_type} exposes a cluster service.",
                service.metadata.namespace,
                service.metadata.name,
            )
        else:
            checks.append({"status": "passed"})

    return checks


def _audit_admission(
    namespaces: list[Any],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    for namespace in namespaces:
        name = namespace.metadata.name
        labels = namespace.metadata.labels or {}
        enforce = labels.get("pod-security.kubernetes.io/enforce")

        if enforce:
            checks.append({"status": "passed"})
        else:
            checks.append({"status": "unknown"})
            _finding(
                findings,
                "pod-security-admission-unset",
                "low",
                "Pod Security Admission enforcement is not declared for this namespace.",
                name,
            )

    return checks


def audit_cluster_security() -> dict[str, Any]:
    _load_kubernetes_config()

    core_v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()

    namespaces = core_v1.list_namespace().items
    pods = core_v1.list_pod_for_all_namespaces().items
    services = core_v1.list_service_for_all_namespaces().items
    policies = networking_v1.list_network_policy_for_all_namespaces().items

    pods_by_namespace: dict[str, list[Any]] = {}
    policies_by_namespace: dict[str, list[Any]] = {}

    for pod in pods:
        pods_by_namespace.setdefault(pod.metadata.namespace, []).append(pod)

    for policy in policies:
        policies_by_namespace.setdefault(policy.metadata.namespace, []).append(policy)

    findings: list[dict[str, Any]] = []

    checks_by_category = {
        "network_policies": _audit_network(
            namespaces,
            pods_by_namespace,
            policies_by_namespace,
            findings,
        ),
        "pod_hardening": _audit_pods(pods, findings),
        "exposure": _audit_exposure(services, findings),
        "admission": _audit_admission(namespaces, findings),
        "supply_chain": [],
    }

    supply_checks = []
    for pod in pods:
        if pod.status.phase in {"Succeeded", "Failed"}:
            continue

        for container in list(pod.spec.containers or []) + list(
            pod.spec.init_containers or []
        ):
            image = container.image or ""
            supply_checks.append(
                {"status": "passed" if "@sha256:" in image else "unknown"}
            )

    checks_by_category["supply_chain"] = supply_checks

    categories = {
        category: _category_result(
            checks,
            CATEGORY_WEIGHTS[category],
        )
        for category, checks in checks_by_category.items()
    }

    applicable_weight = sum(
        result["weight"]
        for result in categories.values()
        if result["score"] is not None
    )

    weighted_score = sum(
        result["score"] * result["weight"]
        for result in categories.values()
        if result["score"] is not None
    )

    security_score = round(weighted_score / applicable_weight) if applicable_weight else None

    total_checks = sum(result["total"] for result in categories.values())
    evaluated_checks = sum(
        result["passed"] + result["failed"]
        for result in categories.values()
    )

    coverage = round((evaluated_checks / total_checks) * 100) if total_checks else 0
    confidence = coverage

    managed_policy = any(
        policy.metadata.labels
        and policy.metadata.labels.get("managed-by") == "k-guard-sentinel"
        for policy in policies
    )

    return {
        "deployed": managed_policy,
        "securityScore": security_score or 0,
        "security_score": security_score,
        "coverage": coverage,
        "confidence": confidence,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "passed": sum(result["passed"] for result in categories.values()),
            "failed": sum(result["failed"] for result in categories.values()),
            "unknown": sum(result["unknown"] for result in categories.values()),
        },
        "categories": categories,
        "findings": findings[:100],
        "scope": {
            "namespaces": len(namespaces),
            "pods": len(pods),
            "services": len(services),
            "network_policies": len(policies),
            "system_namespaces": sorted(SYSTEM_NAMESPACES),
        },
    }
