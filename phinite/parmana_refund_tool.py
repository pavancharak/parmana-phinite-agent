"""Phinite custom tool for a governed customer refund.

Adapter only: Phinite proposes the intent; Parmana is the authority; the
Paytm connector remains outside this repository.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NAMESPACE = "parmana-openai-refund-agent:v1"
POLICY_NAME = "customer-refund"
POLICY_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


def _uuid_from_seed(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    b = bytearray(digest[:16])
    b[6] = (b[6] & 0x0F) | 0x40
    b[8] = (b[8] & 0x3F) | 0x80
    h = bytes(b).hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def _business_transaction_id(order_id: str, txn_id: str) -> str:
    return _uuid_from_seed(f"{NAMESPACE}:{order_id}:{txn_id}")


def _amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("amount must be a valid number") from exc
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    return int(amount) if amount == amount.to_integral_value() else float(amount)


def _required_bool(inputs: dict, name: str) -> bool:
    value = inputs.get(name)
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean supplied by a trusted upstream system")
    return value


def main(inputs, env_variables):
    """Phinite custom-tool entry point.

    Required inputs: order_id, transaction_id, amount, currency, reason,
    refund_eligible, manager_approved, fraud_check_passed.

    The three signals are external business facts. The LLM must never invent
    them from natural-language conversation.
    """
    inputs = inputs or {}
    order_id = str(inputs.get("order_id", "")).strip()
    txn_id = str(inputs.get("transaction_id", "")).strip()
    currency = str(inputs.get("currency", "INR")).strip().upper()
    reason = str(inputs.get("reason", "customer_refund")).strip()

    if not order_id or not txn_id:
        raise ValueError("order_id and transaction_id are required")
    if currency != "INR":
        raise ValueError("Only INR refunds are enabled for the initial demo")
    if not reason:
        raise ValueError("reason is required")

    amount = _amount(inputs.get("amount"))
    refund_eligible = _required_bool(inputs, "refund_eligible")
    manager_approved = _required_bool(inputs, "manager_approved")
    fraud_check_passed = _required_bool(inputs, "fraud_check_passed")

    env = env_variables or {}
    parmana_url = (env.get("PARMANA_API_URL") or os.environ.get("PARMANA_API_URL") or "").rstrip("/")
    api_key = env.get("PARMANA_API_KEY") or os.environ.get("PARMANA_API_KEY")
    principal_id = env.get("PARMANA_PRINCIPAL_ID") or os.environ.get("PARMANA_PRINCIPAL_ID") or "phinite-agent"
    if not parmana_url or not api_key:
        raise RuntimeError("Parmana API configuration is missing")

    business_id = _business_transaction_id(order_id, txn_id)
    authority_id = _uuid_from_seed(f"{business_id}:authority")
    authorization_id = _uuid_from_seed(f"{business_id}:authorization")
    intent_id = _uuid_from_seed(f"{business_id}:intent")
    issued_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # This mirrors the verified BusinessTransaction shape used by the
    # reference OpenAI agent. In particular, refundAmount is bound to the
    # exact amount that appears in the executable intent.
    transaction = {
        "businessTransactionId": business_id,
        "metadata": {
            "businessTransactionId": business_id,
            "integration": "parmana-phinite-agent",
        },
        "authority": {
            "authorityId": authority_id,
            "authorityType": "SERVICE",
            "principalId": principal_id,
            "issuedAt": issued_at,
        },
        "authorization": {
            "authorizationId": authorization_id,
            "authorityId": authority_id,
            "purpose": "Authorize Paytm customer refund (Phinite-proposed intent)",
            "issuedAt": issued_at,
        },
        "intent": {
            "intentId": intent_id,
            "authorizationId": authorization_id,
            "action": "refund",
            "target": order_id,
            "parameters": {
                "orderId": order_id,
                "transactionId": txn_id,
                "amount": amount,
            },
            "createdAt": issued_at,
        },
        "policy": {
            "name": POLICY_NAME,
            "version": POLICY_VERSION,
            "schemaVersion": SCHEMA_VERSION,
        },
        "signals": {
            "refundEligible": refund_eligible,
            "managerApproved": manager_approved,
            "fraudCheckPassed": fraud_check_passed,
            "refundAmount": amount,
        },
        "status": "RECEIVED",
        "createdAt": issued_at,
    }

    body = json.dumps(transaction, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{parmana_url}/execute",
        data=body,
        method="POST",
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        if exc.code == 403:
            try:
                denied = json.loads(raw)
            except json.JSONDecodeError:
                denied = {}
            if denied.get("code") == "POLICY_DENIED":
                return {"output": {"status": "DENIED", "executed": False, "state": "DENIED", "businessTransactionId": business_id, "reason": denied.get("error", "Parmana policy rejected the refund")}}
        if exc.code == 409 or exc.code >= 500:
            return {"output": {"status": "AMBIGUOUS", "executed": False, "state": "UNKNOWN", "businessTransactionId": business_id, "reason": f"Parmana returned HTTP {exc.code}; execution outcome is unknown"}}
        raise RuntimeError(f"Parmana API HTTP {exc.code}: {raw}") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach Parmana: {exc.reason}") from exc

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Parmana returned non-JSON response (HTTP {status})") from exc

    if status != 200:
        raise RuntimeError(f"Unexpected Parmana HTTP status: {status}")

    returned_tx = result.get("transaction")
    if not isinstance(returned_tx, dict) or returned_tx.get("businessTransactionId") != business_id:
        raise RuntimeError("Parmana returned an execution response for a different business transaction")

    executions = result.get("executions")
    if not isinstance(executions, list) or not executions:
        raise RuntimeError("Parmana response contained no execution decision")
    last = executions[-1] if isinstance(executions[-1], dict) else {}
    decision = last.get("decision") if isinstance(last.get("decision"), dict) else {}
    if decision.get("outcome") != "APPROVED":
        raise RuntimeError("Parmana returned HTTP 200 without an APPROVED execution decision")

    auth_envelope = result.get("authorization") if isinstance(result.get("authorization"), dict) else {}
    auth_payload = auth_envelope.get("payload") if isinstance(auth_envelope.get("payload"), dict) else {}
    execution_metadata = last.get("metadata") if isinstance(last.get("metadata"), dict) else {}
    returned_auth_id = auth_payload.get("authorizationId") or execution_metadata.get("authorizationId")
    if not returned_auth_id:
        raise RuntimeError("Parmana APPROVED response did not contain an authorizationId")

    return {
        "output": {
            "status": "APPROVED",
            "executed": True,
            "state": "COMPLETED",
            "businessTransactionId": business_id,
            "authorizationId": returned_auth_id,
            "executionTrustRecord": result,
        },
        "captured_variables": {
            "last_business_transaction_id": business_id,
            "last_parmana_status": "APPROVED",
        },
    }
