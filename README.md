# Parmana × Phinite — Agentic Commerce Refund Demo

## What use case did we build?

> **Agentic commerce refund authorization agent:** a Phinite AI agent understands customer refund requests and extracts the refund intent, while Parmana independently authorizes and governs the consequential refund execution. The agent cannot approve refunds or call Paytm directly. Trusted business signals — refund eligibility, manager approval, and fraud-check status — are supplied separately. Parmana enforces the `paytm:refund` capability and produces execution evidence, with **DENIED → STOP**, **AMBIGUOUS → VERIFY**, and **APPROVED → governed execution**.

### In one sentence

**A customer asks an AI agent for a refund; the AI understands the request, Parmana decides whether the action is authorized, and only an authorized execution path can proceed.**

> **AI can be intelligent without being in charge.**

This repository demonstrates an agentic-commerce refund workflow in which **Phinite provides the AI agent**, while **Parmana remains the independent authorization and execution-governance authority**.

The customer speaks naturally to the AI. The AI understands and proposes the refund intent. Trusted business signals are supplied separately. Parmana authenticates the caller, checks its capability, evaluates the transaction, authorizes or denies execution, and preserves execution evidence.

The AI agent does **not** directly call Paytm and does **not** hold Paytm merchant credentials.

---

# 1. What this demo proves

```text
Customer
   ↓
Phinite Master Agent
   ↓
Refund Intent
   ↓
Trusted Business Context
   ↓
Parmana Authorization
   ├── DENIED → STOP
   ├── AMBIGUOUS → VERIFY
   └── APPROVED
          ↓
     Governed Execution
          ↓
     Business / Paytm Connector
          ↓
     Paytm API
          ↓
     Execution Evidence
```

The central trust boundary is:

```text
AI Agent
   ≠
Authorization Authority
```

Phinite is responsible for understanding the request. Parmana is responsible for determining whether the consequential action is authorized.

---

# 2. Why this matters

A simple agentic architecture can look like:

```text
User → AI Agent → Business API
```

The agent may then become the effective decision-maker for a consequential side effect.

This demo deliberately separates the responsibilities:

```text
User
 ↓
AI Agent
 ↓
Parmana
 ↓
Authorization
 ↓
Execution
```

The principle is:

> **The AI proposes. Parmana authorizes. The business system executes.**

This pattern is applicable beyond refunds to payments, procurement, insurance, financial operations, customer service, and other agentic workflows where an AI action can create a real-world side effect.

---

# 3. What you need

## Required

You need access to:

1. A **Phinite** workspace capable of creating a conversational graph and custom workspace tools.
2. A deployed **Parmana API** with the `/execute` endpoint reachable from Phinite.
3. A Parmana API key for the demo caller.
4. A Parmana principal/caller identity.
5. A downstream business/Paytm connector configured behind Parmana if the demo is intended to exercise the real provider execution path.
6. A browser for the Phinite Graph Studio.
7. For direct API troubleshooting, a terminal. The commands below use Windows PowerShell syntax because that was the environment used to validate this integration.

## Credentials required by the agent

The Phinite refund tool needs:

```env
PARMANA_API_URL=https://parmana-api-real.vercel.app
PARMANA_API_KEY=<secret>
PARMANA_PRINCIPAL_ID=parmana-refund-agents
```

## Credentials the agent must NOT receive

Do not put Paytm merchant credentials in the Phinite agent.

```text
NO PAYTM MERCHANT KEY
NO PAYTM SECRET
NO PAYTM CHECKSUM SECRET
```

Paytm authentication belongs to the downstream connector/execution boundary.

## Secret handling

Never commit real secrets to GitHub. Never paste a secret into a public issue, README, prompt, livestream, or screenshot.

If a credential is exposed, rotate it immediately.

---

# 4. High-level architecture

```text
                    CUSTOMER
                       │
                       ▼
              ┌─────────────────┐
              │  PHINITE AGENT  │
              │                 │
              │ Understand      │
              │ Extract intent  │
              │ Ask questions   │
              └────────┬────────┘
                       │
                       ▼
              Trusted business
                  context
                       │
                       ▼
           ╔══════════════════════╗
           ║       PARMANA        ║
           ║                      ║
           ║ Authentication       ║
           ║ Capability control   ║
           ║ Policy evaluation    ║
           ║ Authorization        ║
           ║ Execution gating     ║
           ║ Evidence             ║
           ║ Verification         ║
           ╚══════════╤═══════════╝
                      │
          ┌───────────┼────────────┐
          │           │            │
        DENIED    AMBIGUOUS     APPROVED
          │           │            │
          ▼           ▼            ▼
         STOP       VERIFY      EXECUTE
                                    │
                                    ▼
                          Business / Paytm
                              connector
                                    │
                                    ▼
                                Evidence
```

---

# 5. Parmana caller and capability

The demo caller is:

```text
parmana-refund-agents
```

Its allowed capability is:

```text
paytm:refund
```

The intended caller configuration is:

```json
{
  "callerId": "parmana-refund-agents",
  "allowedPrincipalIds": ["parmana-refund-agents"],
  "allowedCapabilities": ["paytm:refund"],
  "unrestrictedCapabilities": false
}
```

The capability is intentionally least-privilege.

**Do not use `*`.**

Parmana performs exact capability matching. These are different capabilities:

```text
refund
paytm:refund
```

The transaction intent must therefore use:

```json
"action": "paytm:refund"
```

---

# 6. Verify Parmana before opening Phinite

Before debugging Phinite, verify that the deployed Parmana caller is correctly configured.

In PowerShell:

```powershell
$apiKey = (Get-Content .env | Where-Object { $_ -match '^PARMANA_API_KEY=' }) -replace '^PARMANA_API_KEY=',''
```

Do not print `$apiKey` to the terminal or paste it into chat.

Verify the caller identity and capability:

```powershell
curl.exe -i "https://parmana-api-real.vercel.app/callers/me" `
  -H "Authorization: Bearer $apiKey" `
  -H "Accept: application/json"
```

A correctly configured caller should contain values equivalent to:

```json
{
  "callerId": "parmana-refund-agents",
  "allowedPrincipalIds": [
    "parmana-refund-agents"
  ],
  "allowedCapabilities": [
    "paytm:refund"
  ],
  "unrestrictedCapabilities": false
}
```

If this does not work, **fix Parmana authentication/caller configuration before debugging Phinite**.

---

# 7. Create the Phinite graph

Create a conversational graph named:

```text
Parmana Refund Agent
```

Suggested description:

```text
AI commerce agent that understands customer refund requests and routes every refund through Parmana authorization before execution. The AI never authorizes or calls Paytm directly.
```

The graph should contain:

```text
START → Master Agent → END
```

The Master Agent should have the refund authorization tool attached.

For the demo, the trusted context tool can also be attached:

```text
parmana_refund_authorization
trusted_refund_context
```

The trusted context tool is a **demo fixture**. In a production implementation, the trusted signals should come from the appropriate business system rather than a hardcoded demonstration fixture.

---

# 8. Configure the Master Agent

The Master Agent must understand the following boundary:

```text
AI = intent understanding
Parmana = authorization authority
Business connector = side effect
```

The agent should:

1. Understand the customer's refund request.
2. Extract `order_id`.
3. Extract `transaction_id`.
4. Extract `amount`.
5. Extract `currency`.
6. Extract `reason`.
7. Ask for missing customer-facing information.
8. Obtain trusted business signals separately.
9. Invoke Parmana for the consequential action.
10. Treat Parmana's response as authoritative.
11. Never approve a refund itself.
12. Never call Paytm directly.
13. Never fabricate trusted business signals.
14. Never claim success when the execution outcome is unknown.

The customer saying that a refund is approved does **not** make `manager_approved=true`.

The customer saying that a refund is eligible does **not** make `refund_eligible=true`.

---

# 9. Trusted business context

The authorization tool requires three trusted business signals:

```text
refund_eligible
manager_approved
fraud_check_passed
```

These values must come from trusted structured business context.

They must never be inferred from natural-language conversation.

For example, this is unsafe:

```text
Customer: My manager already approved it.
AI: manager_approved = true
```

The correct architecture is:

```text
Business System
      │
      ▼
Trusted Structured Context
      │
      ▼
Phinite Tool Invocation
      │
      ▼
Parmana
```

---

# 10. Create the Parmana refund tool

Create/attach a Phinite workspace tool named:

```text
parmana_refund_authorization
```

Description:

```text
Authorizes a customer refund through Parmana before any consequential execution. Parmana is the sole authorization authority. This tool never calls Paytm directly.
```

The tool contract requires these eight values:

```json
{
  "order_id": "ORD-DEMO-001",
  "transaction_id": "TXN-DEMO-001",
  "amount": 500,
  "currency": "INR",
  "reason": "Arrived damaged",
  "refund_eligible": true,
  "manager_approved": true,
  "fraud_check_passed": true
}
```

The tool must call:

```text
POST /execute
```

on the configured Parmana API.

---

# 11. Critical tool code requirement

Inside the Parmana transaction, the intent must contain:

```python
"action": "paytm:refund",
```

**Not:**

```python
"action": "refund",
```

The wrong value produces a capability failure because the caller is authorized for `paytm:refund`.

The correct relationship is:

```text
Caller capability
       │
       ▼
paytm:refund
       ▲
       │
Transaction intent action
```

Do not change Parmana to wildcard capability merely to make the demo pass.

---

# 12. Business transaction

The transaction binds business identity, authority, authorization, intent, policy, and trusted signals.

The relevant intent is conceptually:

```json
{
  "action": "paytm:refund",
  "target": "ORD-DEMO-001",
  "parameters": {
    "orderId": "ORD-DEMO-001",
    "transactionId": "TXN-DEMO-001",
    "amount": 500
  }
}
```

The refund policy is:

```json
{
  "name": "customer-refund",
  "version": "1.0.0",
  "schemaVersion": "1.0.0"
}
```

The refund amount must remain bound to the validated intent amount.

---

# 13. Publish the tool

After editing the tool:

1. Save the tool.
2. Click the **Publish** / rocket action.
3. Confirm the new version is published.
4. Return to Graph Studio.
5. Open **Master Agent → Tools**.
6. Confirm `parmana_refund_authorization` is attached.
7. Confirm the published version is the version you intend to test.

A common mistake is editing a draft but running an older published version.

Always verify the version attached to the graph.

---

# 14. Run the end-to-end demo

## Step 1 — Customer request

Enter:

```text
I want a refund of ₹500 for order ORD-DEMO-001 because it arrived damaged.
```

Expected behavior:

The agent understands:

```text
order_id = ORD-DEMO-001
amount = 500
currency = INR
reason = Arrived damaged
```

It should ask for the transaction ID if it is missing.

## Step 2 — Transaction ID

Reply:

```text
The transaction ID is TXN-DEMO-001.
```

## Step 3 — Trusted context

The agent obtains the trusted refund context:

```text
refund_eligible
manager_approved
fraud_check_passed
```

## Step 4 — Parmana

The agent submits the consequential refund intent to Parmana.

Parmana authenticates the caller and evaluates the request.

## Step 5 — Result

The result should be one of:

```text
DENIED
AMBIGUOUS
APPROVED
```

---

# 15. Expected DENIED behavior

```text
Parmana
   ↓
DENIED
   ↓
STOP
```

The agent should tell the customer that Parmana did not authorize the refund.

The agent must not:

- retry with a changed amount
- change the order ID
- fabricate trusted signals
- bypass Parmana
- call Paytm directly
- convert DENIED into APPROVED

This is fail-closed behavior.

---

# 16. Expected AMBIGUOUS behavior

A 409/conflict or another condition where the final execution state cannot be established should be treated as:

```text
AMBIGUOUS
```

The agent must not say:

```text
Refund succeeded.
```

It must also not incorrectly say:

```text
Refund failed.
```

Instead:

```text
Execution outcome is unknown and requires verification.
```

Preserve the Business Transaction ID so the transaction can be verified.

---

# 17. Expected APPROVED behavior

The approved flow is:

```text
Parmana
   ↓
APPROVED
   ↓
Governed Execution
   ↓
Execution Evidence
```

The agent may report the Parmana authorization and the execution state returned by Parmana.

For a public claim that the provider-side refund actually settled, verify the downstream provider result separately. `APPROVED` establishes Parmana authorization; provider-side settlement must be supported by provider evidence.

---

# 18. Successful demo transaction

A fresh end-to-end demonstration was completed using:

```text
Order ID:              ORD-DEMO-001
Transaction ID:        TXN-DEMO-001
Amount:                ₹500
Reason:                Arrived damaged
```

Parmana returned:

```text
Decision:              APPROVED
Authorization ID:     69abe6c1-48af-483a-8774-4783cb2ca31d
Business Transaction: e8a7d9ed-7942-4a73-897d-d1b3577347ef
```

The Phinite agent reported the execution as complete.

Keep these IDs as demonstration evidence, but use **fresh IDs for future runs**.

---

# 19. Direct Parmana smoke test

When the Phinite layer is suspected, test Parmana directly.

Create a file named:

```text
test-refund.json
```

with a valid UUID and the correct capability:

```json
{
  "businessTransactionId": "00000000-0000-4000-8000-000000000001",
  "authority": {
    "authorityId": "00000000-0000-4000-8000-000000000002",
    "authorityType": "SERVICE",
    "principalId": "parmana-refund-agents",
    "issuedAt": "2026-01-01T00:00:00.000Z"
  },
  "authorization": {
    "authorizationId": "00000000-0000-4000-8000-000000000003",
    "authorityId": "00000000-0000-4000-8000-000000000002",
    "purpose": "Authorize Paytm customer refund",
    "issuedAt": "2026-01-01T00:00:00.000Z"
  },
  "intent": {
    "intentId": "00000000-0000-4000-8000-000000000004",
    "authorizationId": "00000000-0000-4000-8000-000000000003",
    "action": "paytm:refund",
    "target": "ORD-SMOKE-001",
    "parameters": {
      "orderId": "ORD-SMOKE-001",
      "transactionId": "TXN-SMOKE-001",
      "amount": 500
    }
  },
  "policy": {
    "name": "customer-refund",
    "version": "1.0.0",
    "schemaVersion": "1.0.0"
  },
  "signals": {
    "refundEligible": true,
    "managerApproved": true,
    "fraudCheckPassed": true,
    "refundAmount": 500
  },
  "status": "RECEIVED"
}
```

Then run:

```powershell
curl.exe -i "https://parmana-api-real.vercel.app/execute" `
  -H "Authorization: Bearer $apiKey" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json" `
  --data-binary "@test-refund.json"
```

Use a **fresh business transaction ID** for repeated tests. Do not assume that reusing a previous transaction is equivalent to a new execution.

---

# 20. PowerShell troubleshooting: malformed JSON

PowerShell's `curl` alias/argument handling can make JSON POST debugging confusing.

Prefer:

```powershell
curl.exe
```

rather than relying on the PowerShell alias.

For larger JSON bodies, write the body to a file and use:

```powershell
--data-binary "@test-refund.json"
```

This avoids quoting and escaping problems.

A malformed request can produce HTTP 400 even when Parmana itself is healthy.

---

# 21. Troubleshooting matrix

| Symptom | Likely cause | What to check | Correct response |
|---|---|---|---|
| `authentication required` | Missing/invalid API key | `PARMANA_API_KEY`, Authorization header | Fix the secret; do not paste it into chat |
| `CAPABILITY_NOT_ALLOWED` | Action does not match caller capability | `allowedCapabilities` and transaction `intent.action` | Use `paytm:refund`; do not use `*` |
| `Caller is not permitted to invoke this capability` | Same capability mismatch | `/callers/me` and tool code | Align action with authorized capability |
| `businessTransactionId must be a valid UUID` | Invalid transaction ID | Request body | Generate/use a valid UUID |
| `order_id and transaction_id are required` | Tool received incomplete input | Phinite tool invocation/logs | Verify agent arguments and tool contract |
| `jsonInput: {}` | Direct runner supplied empty input | Phinite execution log | Test through the graph and verify tool input configuration |
| Phinite shows green `SUCCESS` but result contains traceback | Wrapper completed, tool failed | Execution log result | Inspect actual tool result, not wrapper status |
| HTTP 400 | Malformed request/body/schema | Raw response body and JSON | Fix request formatting/schema |
| HTTP 403 | Authentication/capability/authorization issue | Response `code`, caller scope | Inspect exact error; do not bypass policy |
| HTTP 409 | Execution state is uncertain/conflict | Response body and Business Transaction ID | Treat as `AMBIGUOUS`; verify before retrying |
| HTTP 5xx | Server/downstream failure | Parmana deployment logs | Treat final outcome as unknown until verified |
| Agent invents trusted signals | Prompt/runtime boundary violation | Tool inputs and trusted context source | Only accept structured trusted business context |
| Agent calls Paytm directly | Architecture violation | Agent tools/credentials | Remove Paytm access from agent |
| Edited code but old behavior persists | Old tool version still attached | Published version + Master Agent Tools | Publish and confirm attached version |
| `refund` action rejected | Wrong capability name | `intent.action` | Change only to `paytm:refund` |
| `APPROVED` but provider result is `UNKNOWN` | Parmana authorized but provider outcome is uncertain | Execution evidence/provider response | Do not claim provider settlement |

---

# 22. Troubleshooting order

Always troubleshoot in this order.

## A. Check Parmana authentication

```powershell
curl.exe -i "https://parmana-api-real.vercel.app/callers/me" `
  -H "Authorization: Bearer $apiKey" `
  -H "Accept: application/json"
```

## B. Check caller capability

Confirm:

```text
callerId = parmana-refund-agents
allowedCapabilities = paytm:refund
```

## C. Check tool version

In Phinite:

```text
Graph Studio
 → Master Agent
 → Tools
 → parmana_refund_authorization
```

Confirm the published version is current.

## D. Check the action

Search the tool code for:

```text
"action"
```

It must be:

```text
"action": "paytm:refund"
```

## E. Check arguments

The tool invocation must contain all eight required inputs.

## F. Check the Parmana response

Read the actual HTTP status and response body.

Do not rely only on a UI label such as `SUCCESS`.

## G. Check downstream evidence

If Parmana returns APPROVED, inspect the execution/provider evidence before making a provider-side success claim.

---

# 23. Important integration failures discovered during development

## Failure 1 — Empty tool arguments

The first direct Phinite tool-runner tests supplied:

```json
{
  "jsonInput": {}
}
```

The Python tool required `order_id` and `transaction_id`, resulting in:

```text
ValueError: order_id and transaction_id are required
```

Lesson:

> A tool's Python schema/code and the actual Phinite runtime invocation must both be aligned.

A Python `INPUT_SCHEMA` declaration by itself does not guarantee that a direct runner will populate its test input object.

---

## Failure 2 — Wrong capability

An earlier tool generated:

```python
"action": "refund",
```

The Parmana caller was authorized for:

```text
paytm:refund
```

Parmana correctly rejected the call.

The fix was:

```python
"action": "paytm:refund",
```

No wildcard capability was introduced.

---

## Failure 3 — HTTP 409

An earlier transaction returned HTTP 409.

The correct agent behavior was:

```text
AMBIGUOUS
```

rather than:

```text
SUCCESS
```

or:

```text
FAILURE
```

Lesson:

> **Unknown execution state must remain unknown until verified.**

---

## Failure 4 — PowerShell request formatting

An early direct API test used PowerShell `curl` with a JSON variable and resulted in a malformed JSON request.

The reliable Windows pattern used for this demo is:

```powershell
curl.exe -i "https://parmana-api-real.vercel.app/execute" `
  -H "Authorization: Bearer $apiKey" `
  -H "Content-Type: application/json" `
  -H "Accept: application/json" `
  --data-binary "@test-refund.json"
```

---

# 24. Fresh transaction IDs

For repeat demonstrations, use a new order/transaction pair.

Example:

```text
ORD-DEMO-002
TXN-DEMO-002
```

Do not blindly reuse a transaction that already produced an execution result.

If the system reports a conflict or ambiguous state, preserve the Business Transaction ID and verify it rather than creating a second execution simply because the first result is inconvenient.

---

# 25. Demo safety and security rules

Before every public demonstration:

- Do not display API keys.
- Do not display `.env` contents.
- Do not expose Paytm credentials.
- Do not give Paytm credentials to the AI agent.
- Do not use wildcard capability `*`.
- Use fresh demo transaction identifiers.
- Use demo/sandbox business data where appropriate.
- Redact authorization secrets from screenshots.
- Verify provider-side outcome before claiming a real refund settled.

If a secret has been exposed, rotate it before continuing.

---

# 26. Public demo script

## Opening

Say:

> “This is a Phinite AI agent connected to Parmana.”
>
> “The customer is going to ask for a refund.”
>
> “The important part is that the AI is not the authorization authority.”

## Customer request

Enter:

```text
I want a refund of ₹500 for order ORD-DEMO-001 because it arrived damaged.
```

Say:

> “The AI understands the customer's intent, but understanding the request does not give the AI authority to execute it.”

## Transaction ID

Enter:

```text
The transaction ID is TXN-DEMO-001.
```

Say:

> “The agent now has the customer-facing information required to construct the refund intent.”

## Parmana

When Parmana is invoked, say:

> “This is the authorization boundary.”
>
> “The AI is not saying APPROVED. Parmana is saying APPROVED.”

Show:

```text
APPROVED
Authorization ID
Business Transaction ID
```

Then show execution/evidence.

---

# 27. One-minute version

> “I'm going to ask an AI agent to refund ₹500.”
>
> “The agent understands the request and extracts the order and transaction details.”
>
> “But the agent does not have authority to execute the refund.”
>
> “It sends the intent to Parmana.”
>
> “Parmana authenticates the caller, checks its capability, evaluates the request, and either denies it, marks it ambiguous, or approves it.”
>
> “In this case Parmana approved the transaction.”
>
> “The authorized execution path then proceeds and produces execution evidence.”
>
> “That's the distinction: the AI can be intelligent without being in charge.”

---

# 28. What to show on screen

For a technical demonstration, show:

1. Phinite Graph Studio: `START → Master Agent → END`.
2. Master Agent → Tools.
3. `parmana_refund_authorization` attached.
4. Tool code showing `"action": "paytm:refund"`.
5. Customer request.
6. Trusted business context invocation.
7. Parmana `APPROVED` response.
8. Authorization ID.
9. Business Transaction ID.
10. Execution/trust evidence.

Never show secrets.

---

# 29. Demo checklist

## Before the demo

- [ ] Phinite workspace accessible.
- [ ] Parmana API deployed.
- [ ] Parmana `/execute` reachable.
- [ ] Parmana caller configured.
- [ ] `parmana-refund-agents` exists.
- [ ] `paytm:refund` is allowed.
- [ ] No wildcard capability is being used.
- [ ] Parmana API key is stored as a secret.
- [ ] Paytm credentials are not present in the Phinite agent.
- [ ] Trusted business context is available.
- [ ] Refund tool is published.
- [ ] Correct published version is attached to the Master Agent.
- [ ] Tool uses `paytm:refund`.
- [ ] Fresh demo order and transaction IDs are ready.
- [ ] Provider-side execution path is available if claiming a real provider action.

## During the demo

- [ ] Customer request understood.
- [ ] Missing transaction ID requested.
- [ ] Trusted signals obtained from structured context.
- [ ] Parmana invoked.
- [ ] Authorization result displayed.
- [ ] Business Transaction ID captured.
- [ ] Execution evidence displayed.
- [ ] Provider result verified before claiming settlement.

## If something fails

- [ ] Do not weaken Parmana capability policy.
- [ ] Do not give the agent Paytm credentials.
- [ ] Do not fabricate business signals.
- [ ] Do not retry a DENIED transaction with altered parameters.
- [ ] Treat 409/unknown states as AMBIGUOUS.
- [ ] Inspect the actual HTTP response and logs.

---

# 30. What this achieves

This is not merely a demonstration that an AI agent can call an API.

It demonstrates a separation of responsibilities for consequential agentic actions.

```text
Phinite / AI
 ├── understanding
 ├── reasoning
 ├── intent extraction
 └── conversation

Trusted Business Context
 └── authoritative business facts

Parmana
 ├── authentication
 ├── capability control
 ├── authorization
 ├── policy evaluation
 ├── execution gating
 ├── evidence
 └── verification

Business Connector
 └── provider side effect
```

The architecture creates an explicit boundary between probabilistic AI behavior and deterministic business authority.

---

# 31. Final architecture

```text
                         CUSTOMER
                            │
                            ▼
                 ┌────────────────────┐
                 │   PHINITE AGENT    │
                 │                    │
                 │ Understand         │
                 │ Extract intent     │
                 │ Ask questions      │
                 │                    │
                 │ NO AUTHORITY       │
                 └─────────┬──────────┘
                           │
                           │ Refund Intent
                           ▼
                 ┌────────────────────┐
                 │ TRUSTED CONTEXT    │
                 │                    │
                 │ refund_eligible    │
                 │ manager_approved   │
                 │ fraud_check_passed │
                 └─────────┬──────────┘
                           │
                           ▼
              ╔══════════════════════════╗
              ║         PARMANA          ║
              ║                          ║
              ║ Authentication           ║
              ║ Capability Authorization ║
              ║ Policy Evaluation        ║
              ║ Authorization            ║
              ║ Execution Gating         ║
              ║ Evidence                 ║
              ║ Verification             ║
              ╚════════════╤═════════════╝
                           │
             ┌─────────────┼──────────────┐
             │             │              │
             ▼             ▼              ▼
          DENIED       AMBIGUOUS       APPROVED
             │             │              │
             ▼             ▼              ▼
            STOP        VERIFY        EXECUTE
                                          │
                                          ▼
                                ┌──────────────────┐
                                │ BUSINESS / PAYTM │
                                │ CONNECTOR        │
                                └────────┬─────────┘
                                         │
                                         ▼
                                EXECUTION EVIDENCE
```

---

# 32. Core positioning

> **AI can be intelligent without being in charge.**

> **The AI proposes. Parmana authorizes. The business system executes.**

> **Parmana is the execution-authorization layer for agentic commerce.**

The refund is the concrete consequential action used to demonstrate the architecture. The broader system is about giving AI agents a controlled path to act without making the AI itself the ultimate authority over what it is allowed to do.

---

# 33. Reproducibility status

The current documented baseline reflects the working Phinite × Parmana demonstration, including the integration issues discovered and resolved during development.

The successful demonstration used:

```text
Phinite Master Agent
        ↓
Parmana refund authorization tool
        ↓
Parmana capability: paytm:refund
        ↓
Parmana APPROVED
        ↓
Governed execution
        ↓
Execution evidence
```

Future changes should be treated as new versions of the demo rather than silently changing the documented baseline.
