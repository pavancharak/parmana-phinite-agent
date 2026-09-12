# Parmana × Phinite — Agentic Commerce Refund Demo

Autonomous AI commerce agent built on Phinite, with **Parmana as the independent execution-authorization layer**.

> **AI can be intelligent without being in charge.**

This repository demonstrates an end-to-end agentic-commerce refund flow in which an AI agent understands a customer request and proposes the consequential action, while Parmana independently authorizes and governs whether the action may execute.

---

## 1. What this demo proves

The customer interacts with a Phinite AI agent:

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

The critical separation is:

```text
AI Agent
   ≠
Authorization Authority
```

Phinite understands the request. Parmana determines whether the consequential action is authorized.

The agent does **not** directly call Paytm and does **not** hold Paytm merchant credentials.

---

## 2. Why this matters

A conventional agentic workflow can look like:

```text
User → AI Agent → Business API
```

That gives the agent a path from natural-language reasoning directly to a consequential side effect.

This demo separates those responsibilities:

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

The design goal is simple:

> The AI can understand and propose the action without becoming the authority over whether that action is allowed.

---

## 3. Components

### Phinite

Phinite provides the agent runtime.

The Master Agent:

- understands the customer's request
- extracts refund intent
- asks for missing customer-facing information
- obtains trusted business context
- invokes the Parmana refund tool
- treats Parmana's response as authoritative

### Parmana

Parmana provides the authorization and execution-governance boundary.

It handles:

- caller authentication
- capability authorization
- business transaction creation
- policy evaluation
- authorization
- execution gating
- execution evidence
- verification

The relevant execution capability is:

```text
paytm:refund
```

### Paytm connector / business execution path

The downstream connector is reached only through the Parmana-governed execution path. The Phinite agent must not call Paytm directly.

---

## 4. Repository architecture

```text
parmana-phinite-agent
        │
        │ Phinite integration
        ▼
   Parmana API
        │
        │ Authorization + execution governance
        ▼
 Paytm / business connector
        │
        ▼
    Paytm API
```

The agent-side trust boundary is:

```text
Phinite Agent
     │
     │ Parmana /execute
     ▼
  Parmana
     │
     │ authorized execution
     ▼
Paytm connector
```

---

## 5. Security model

The Phinite integration needs Parmana credentials, not Paytm credentials.

```text
Phinite
 ├── PARMANA_API_URL
 ├── PARMANA_API_KEY
 └── PARMANA_PRINCIPAL_ID

NO:
 ├── PAYTM merchant credentials
 └── PAYTM secrets in agent code
```

Never commit secrets to this repository, paste them into prompts, or expose them in screenshots or livestreams.

If a credential is exposed publicly, rotate it.

---

## 6. Environment variables

Configure these as Phinite secrets / environment variables:

```env
PARMANA_API_URL=https://parmana-api-real.vercel.app
PARMANA_API_KEY=<secret>
PARMANA_PRINCIPAL_ID=parmana-refund-agents
```

Do not place real secret values in this README.

---

## 7. Parmana caller configuration

The deployed demo caller is:

```text
parmana-refund-agents
```

Its allowed capability is explicitly scoped to:

```text
paytm:refund
```

The intended shape is:

```json
{
  "callerId": "parmana-refund-agents",
  "allowedPrincipalIds": ["parmana-refund-agents"],
  "allowedCapabilities": ["paytm:refund"],
  "unrestrictedCapabilities": false
}
```

Do **not** use `*` as a capability just to make the integration work. Capability authorization is intentionally least-privilege and exact.

---

## 8. Phinite graph

Create a conversational graph named:

```text
Parmana Refund Agent
```

Suggested description:

```text
AI commerce agent that understands customer refund requests and routes every refund through Parmana authorization before execution. The AI never authorizes or calls Paytm directly.
```

The graph should be:

```text
START → Master Agent → END
```

The Master Agent should use the configured model and have these workspace tools attached:

```text
parmana_refund_authorization
trusted_refund_context
```

`trusted_refund_context` is demo context and should be treated as trusted structured business data, not as a value inferred from the customer conversation.

---

## 9. Master Agent responsibilities

The agent should:

1. Understand the customer's refund request.
2. Extract `order_id`, `transaction_id`, `amount`, `currency`, and `reason`.
3. Ask for missing customer-facing information when necessary.
4. Obtain trusted values for:
   - `refund_eligible`
   - `manager_approved`
   - `fraud_check_passed`
5. Invoke Parmana for the consequential refund action.
6. Treat Parmana's decision as authoritative.
7. Never authorize the refund itself.
8. Never call Paytm directly.
9. Never fabricate trusted business signals.
10. Never claim success when the execution outcome is unknown.

The customer saying that a refund is eligible or approved does not itself establish those trusted business signals.

---

## 10. Refund tool contract

The Phinite workspace tool is:

```text
parmana_refund_authorization
```

It should accept these eight inputs:

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

The tool calls Parmana's:

```text
POST /execute
```

The transaction intent must contain exactly:

```json
{
  "action": "paytm:refund"
}
```

### Important capability detail

Do **not** use:

```json
{"action":"refund"}
```

The deployed caller is authorized for `paytm:refund`, and Parmana performs exact capability matching. Using `refund` caused the expected fail-closed response:

```text
Caller is not permitted to invoke this capability.
```

The correct action is:

```text
paytm:refund
```

Do not solve capability mismatches by granting wildcard access.

---

## 11. Business transaction structure

The Parmana transaction binds the business identity, authority, authorization, intent, policy, and trusted signals.

The important intent is conceptually:

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

The policy used by the refund integration is:

```json
{
  "name": "customer-refund",
  "version": "1.0.0",
  "schemaVersion": "1.0.0"
}
```

The trusted signals are bound to the transaction, including the refund amount.

---

# 12. How to run the live demo

## Step 1 — Open Phinite

Open the Phinite workspace and go to **Graph Studio**.

Open:

```text
Parmana Refund Agent
```

Verify the graph:

```text
START
  ↓
Master Agent
  ↓
END
```

---

## Step 2 — Verify the Master Agent tools

Open:

```text
Master Agent → Tools
```

Verify:

```text
parmana_refund_authorization
trusted_refund_context
```

Open the refund tool and confirm the published version is the one you intend to run.

---

## Step 3 — Verify the refund action

Open the tool code and confirm the Parmana transaction contains:

```python
"action": "paytm:refund",
```

Save and publish the tool if needed.

---

## Step 4 — Start the customer conversation

Enter:

```text
I want a refund of ₹500 for order ORD-DEMO-001 because it arrived damaged.
```

The agent should extract:

```text
order_id = ORD-DEMO-001
amount = 500
currency = INR
reason = Arrived damaged
```

Because the transaction ID is not yet known, the agent should ask for it.

---

## Step 5 — Provide the transaction ID

Reply:

```text
The transaction ID is TXN-DEMO-001.
```

The agent now has the customer-facing refund information required to submit the request through Parmana.

---

## Step 6 — Obtain trusted business context

The agent retrieves the trusted refund context.

The relevant business signals are:

```text
refund_eligible
manager_approved
fraud_check_passed
```

These must come from trusted structured context. They must not be inferred from the customer's message.

---

## Step 7 — Parmana authorization

The agent sends the refund intent to the deployed Parmana API.

Conceptually:

```text
POST /execute
Authorization: Bearer <PARMANA_API_KEY>
```

The caller is:

```text
parmana-refund-agents
```

The requested capability is:

```text
paytm:refund
```

Parmana becomes the authority for the consequential action.

---

# 13. Expected outcomes

## DENIED

```text
Parmana
   ↓
DENIED
   ↓
STOP
```

The agent must explain that Parmana did not authorize the refund.

It must not:

- retry with changed parameters
- invent different signals
- bypass Parmana
- call Paytm directly

---

## AMBIGUOUS

If Parmana returns a conflict / unknown state, the agent should report:

```text
AMBIGUOUS
```

and require verification.

It must not claim either success or failure until the final state is known.

A real test during integration returned HTTP 409, and the agent correctly surfaced the transaction as ambiguous instead of hallucinating success.

---

## APPROVED

The successful path is:

```text
Parmana
   ↓
APPROVED
   ↓
Governed Execution
   ↓
Execution Evidence
```

Only an approved decision permits the governed execution path to proceed.

---

# 14. Successful demonstration

A fresh end-to-end test was completed with:

```text
Order ID:              ORD-DEMO-001
Transaction ID:        TXN-DEMO-001
Amount:                ₹500
Reason:                Arrived damaged

Parmana decision:      APPROVED
Authorization ID:      69abe6c1-48af-483a-8774-4783cb2ca31d
Business Transaction:  e8a7d9ed-7942-4a73-897d-d1b3577347ef
```

The Phinite agent reported that the refund execution was complete.

### Verification note

For a public claim that a real provider-side refund succeeded, verify the downstream provider/Paytm result for the same Business Transaction ID. An authorization `APPROVED` result is evidence that Parmana allowed execution; it should not be conflated with provider-side settlement success when the downstream outcome is still unknown.

---

# 15. Live demo script

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

Explain:

> “The agent understands the request and extracts the intent, but it does not have authority to approve the refund.”

## Transaction ID

Enter:

```text
The transaction ID is TXN-DEMO-001.
```

Explain:

> “Now the agent has the customer-facing transaction information required to construct the request.”

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

Then show the execution/evidence record where available.

---

# 16. What to show on screen

For a technical demo, show:

1. Phinite Graph Studio with `START → Master Agent → END`.
2. Master Agent → Tools with the refund tool attached.
3. The refund tool code containing `"action": "paytm:refund"`.
4. The customer conversation with a fresh demo order and transaction ID.
5. The Parmana `APPROVED` response.
6. The Authorization ID.
7. The Business Transaction ID.
8. The resulting execution/evidence record.

Never show API keys, Paytm credentials, `.env` contents, or other secrets.

---

# 17. Integration lessons discovered during the build

## Empty tool arguments

The first direct Phinite tool-runner tests supplied an empty JSON input object while the Python function required `order_id` and `transaction_id`, producing:

```text
ValueError: order_id and transaction_id are required
```

The working graph path required the tool's invocation contract and actual agent-provided arguments to be aligned.

## Wrong capability name

An earlier generated tool used:

```python
"action": "refund",
```

The deployed Parmana caller was scoped to:

```text
paytm:refund
```

Parmana correctly rejected the mismatch. The fix was to use:

```python
"action": "paytm:refund",
```

without weakening Parmana's caller capability policy.

## Unknown execution outcome

One earlier transaction returned HTTP 409. The correct behavior was to report `AMBIGUOUS` and preserve the Business Transaction ID instead of claiming success.

These failures were useful validation of the fail-closed governance boundary.

---

# 18. What this achieves

This is more than a demonstration that an AI agent can call an API.

The demo shows that an AI agent can participate in consequential commerce while an independent authorization layer controls whether execution is permitted.

The division is:

```text
Phinite / AI
 ├── understanding
 ├── reasoning
 ├── intent extraction
 └── conversation

Parmana
 ├── authority
 ├── authentication
 ├── capability control
 ├── authorization
 ├── execution gating
 ├── evidence
 └── verification

Business connector
 └── actual provider side effect
```

---

# 19. Core positioning

> **AI can be intelligent without being in charge.**

A concise description of the system is:

> **The AI proposes. Parmana authorizes. The business system executes.**

Or:

> **AI can be intelligent without being in charge. Parmana is the execution-authorization layer for agentic commerce.**

---

# 20. One-minute demo version

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

# 21. Demo checklist

Before a live run:

- [ ] Parmana API is deployed and reachable.
- [ ] Phinite graph is saved.
- [ ] Master Agent is configured.
- [ ] `parmana_refund_authorization` is attached.
- [ ] `trusted_refund_context` is available when using the demo fixture.
- [ ] Refund tool is published.
- [ ] Transaction action is `paytm:refund`.
- [ ] Caller is `parmana-refund-agents`.
- [ ] Caller capability is `paytm:refund`.
- [ ] No wildcard `*` capability is used.
- [ ] No Paytm credentials are present in the Phinite agent.
- [ ] Parmana API key is stored as a secret.
- [ ] Fresh demo order and transaction IDs are used.
- [ ] Authorization ID is captured.
- [ ] Business Transaction ID is captured.
- [ ] Execution evidence is available.
- [ ] Provider-side success is verified before claiming a real-world refund settled successfully.

---

# 22. Final architecture

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

## The point of the demo

The refund is the consequential action used to demonstrate the control architecture.

The broader pattern is:

```text
AI Agent
   +
Independent Authorization
   +
Deterministic Execution Governance
   +
Execution Evidence
```

That is the foundation for agentic commerce where agents can act without becoming the ultimate authority over what they are allowed to do.
