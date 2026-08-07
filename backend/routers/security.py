import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend import database
from .auth import verify_token

router = APIRouter(prefix="/security", tags=["Runtime Security"])
logger = logging.getLogger("k-guard-backend")


def _event_id(payload: dict) -> str:
    source_id = (
        payload.get("eventId")
        or payload.get("event_id")
        or payload.get("time")
        or payload.get("timestamp")
        or json.dumps(payload, sort_keys=True)
    )

    return hashlib.sha256(
        f"falco:{source_id}".encode("utf-8")
    ).hexdigest()[:32]


def _normalize_payload(payload: dict) -> dict:
    output = payload.get("output") or payload.get("message") or ""
    priority = payload.get("priority") or payload.get("severity") or "INFO"
    rule_name = payload.get("rule") or payload.get("rule_name") or "unknown"

    return {
        "event_id": _event_id(payload),
        "source": str(payload.get("source") or "falco"),
        "severity": str(priority),
        "message": str(output),
        "rule_name": str(rule_name),
        "priority": str(priority),
        "output": str(output),
        "raw_payload": json.dumps(payload, ensure_ascii=False),
    }


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_security_event(request: Request):
    expected_token = os.getenv("FALCO_INGEST_TOKEN")

    if expected_token:
        received_token = request.headers.get("X-KGuard-Ingest-Token", "")

        if received_token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Falco ingestion token",
            )

    try:
        payload = await request.json()
    except Exception as error:
        logger.warning("Invalid security event JSON: %s", error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    if isinstance(payload, dict):
        payloads = [payload]
    elif isinstance(payload, list):
        payloads = payload
    else:
        payloads = []

    if not payloads or not all(isinstance(item, dict) for item in payloads):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security event must be a JSON object or an array of objects",
        )

    conn = None
    inserted_count = 0
    event_ids = []

    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()

        for payload_item in payloads:
            event = _normalize_payload(payload_item)
            now = datetime.now(timezone.utc).isoformat()

            try:
                cursor.execute(
                    """
                    INSERT INTO security_events (
                        event_id,
                        source,
                        severity,
                        message,
                        rule_name,
                        priority,
                        output,
                        raw_payload,
                        ai_status,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    """,
                    (
                        event["event_id"],
                        event["source"],
                        event["severity"],
                        event["message"],
                        event["rule_name"],
                        event["priority"],
                        event["output"],
                        event["raw_payload"],
                        now,
                        now,
                    ),
                )

                inserted_count += 1
                event_ids.append(event["event_id"])

            except sqlite3.IntegrityError:
                continue

        conn.commit()

    except Exception:
        if conn:
            conn.rollback()

        logger.exception("Security event persistence failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security event persistence failed",
        )

    finally:
        if conn:
            conn.close()

    logger.info(
        "Falco batch persisted: received=%s inserted=%s",
        len(payloads),
        inserted_count,
    )

    return {
        "status": "accepted",
        "received": len(payloads),
        "inserted": inserted_count,
        "event_ids": event_ids[:10],
        "event_ids_truncated": len(event_ids) > 10,
        "ai_status": "pending",
    }


@router.get("/alerts")
async def get_runtime_alerts(
    limit: int = 50,
    user: dict = Depends(verify_token),
):
    limit = max(1, min(limit, 100))
    conn = None

    try:
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                event_id,
                source,
                severity,
                message,
                rule_name,
                priority,
                output,
                raw_payload,
                ai_status,
                ai_enrichment,
                created_at,
                updated_at
            FROM security_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]

    except Exception:
        logger.exception("Security alerts SQLite query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security event query failed",
        )

    finally:
        if conn:
            conn.close()
