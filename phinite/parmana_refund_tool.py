"""Phinite custom tool: authorize and execute a refund through Parmana.

This tool is intentionally the only consequential action boundary exposed to the
Phinite agent. It never calls Paytm and never contains Paytm credentials.
"""

import hashlib
import json
import os
import uuid
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _deterministic_business_transaction_id(order_id: str, transaction_id: str) -> str:
    """Create a stable UUID from the same logical replay key on every run."""
    digest = hashlib.sha256(f"{order_id}:{transaction_id}".encode("utf-8")).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def _money(value) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("amount must be a valid decimal number") from exc
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    return format(amount, "f")


def _require_bool(inputs: dict, name: str) -> bool:
    value = inputs.get(name)
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean supplied by a trusted upstream source")
    return value


def main(inputs, env_variables):
    """Phinite custom-tool entry point.

    Expected inputs:
      order_id, transaction_id, amount, currency, reason,
      refund_eligible, manager_approved, fraud_check_passed

    The three approval signals must be supplied as structured booleans. The LLM
    must never infer or invent them from conversational text.
    """
    inputs = inputs or {}

    order_id = str(inputs.get("order_id", "")).strip()
    transaction_id = str(inputs.get("transaction_id", "")).strip()
    currency = str(inputs.get("currency", "INR")).strip().upper()
    reason = str(inputs.get("reason", "customer_refund")).strip()

    if not order_id or not transaction_id:
        raise ValueError("order_id and transaction_id are required")
    if currency != "INR":
        raise ValueError("Only INR refunds are enabled in the initial demo")
    if not reason:
        raise ValueError("reason is required")

    amount = _money(inputs.get("amount"))
    refund_eligible = _require_bool(inputs, "refund_eligible")
    manager_approved = _require_bool(inputs, "manager_approved")
    fraud_check_passed = _require_bool(inputs, "fraud_check_passed")

    # Phinite provides secrets through env_variables. Fall back to process env
    # for local testing only; no secret is ever hardcoded.
    env = env_variables or {}
    parmana_url = (env.get("PARMANA_API_URL") or os.environ.get("PARMANA_API_URL") or "").rstrip("/")
    api_key = env.get("PARMANA_API_KEY") or os.environ.get("PARMANA_API_KEY")
    principal_id = env.get("PARMANA_PRINCIPAL_ID") or os.environ.get("PARMANA_PRINCIPAL_ID") or "phinite-agent"

    if not parmana_url or not api_key:
        raise RuntimeError("Parmana API configuration is missing")

    business_transaction_id = _deterministic_business_transaction_id(order_id, transaction_id)

    payload = {
        "businessTransaction": {
            "businessTransactionId": business_transaction_id,
            "capability": "paytm:refund",
            "parameters": {
                "orderId": order_id,
                "transactionId": transaction_id,
                "amount": amount,
                "currency": currency,
                "reason": reason,
            },
            "policy": {"name": "customer-refund", "version": "1.0.0"},
            "signals": {
                "refundEligible": refund_eligible,
                "managerApproved": manager_approved,
                "fraudCheckPassed": fraud_check_passed,
            },
            "principalId": principal_id,
        }
    }

    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{parmana_url}/execute",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
        if status == 403:
            return {"output": {"status": "DENIED", "executed": False, "state": "DENIED", "reason": raw}}
        if status == 409:
            return {"output": {"status": "AMBIGUOUS", "executed": False, "state": "UNKNOWN", "reason": "Replay or conflicting execution response", "raw": raw}}
        raise RuntimeError(f"Parmana request failed with HTTP {status}: {raw}")
    except URLError as exc:
        raise RuntimeError(f"Unable to reach Parmana: {exc.reason}") from exc

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Parmana returned non-JSON response") from exc

    # Do not reinterpret authorization. Return Parmana's signed execution
    # evidence to the agent so the conversational layer can explain the result.
    if status != 200:
        raise RuntimeError(f"Unexpected Parmana HTTP status: {status}")

    return {
        "output": {
            "status": "APPROVED",
            "executed": True,
            "state": "COMPLETED",
            "businessTransactionId": business_transaction_id,
            "parmana": result,
        },
        "captured_variables": {
            "last_business_transaction_id": business_transaction_id,
            "last_parmana_status": "APPROVED",
        },
    }
