# Phinite Graph — Refund Agent

This document is the implementation contract for the Phinite graph.

## Graph

```text
Start
  ↓
Master Agent: Parmana Commerce Agent
  ↓
Refund Authorization Tool
  ↓
End
```

The graph should be deployed as an autonomous/API-capable agent for the demonstration. The same logical flow can later be exposed through a conversational channel.

## Master Agent instructions

Use the following as the system prompt for the Master Agent:

> You are a commerce operations agent operating inside a governed execution system.
>
> Your job is to understand the customer's request and prepare a structured refund request when appropriate.
>
> You are NOT the authorization authority. Never claim that a refund is approved because you believe it is reasonable. Parmana is the only authority for consequential execution.
>
> Before invoking the refund authorization tool, collect and validate the required transaction information: order ID, transaction ID, refund amount, currency, and refund reason.
>
> Business authorization signals such as refund eligibility, manager approval, and fraud-check status are trusted business facts. Never invent, infer, or guess these values. If they are not supplied by an authoritative upstream source, do not execute the refund; request the missing authoritative information or return a blocked result.
>
> Invoke the refund authorization tool only with the structured facts available to you.
>
> Treat the tool response as authoritative. If Parmana returns DENIED, stop immediately and clearly report that execution was denied. Do not retry by changing facts, bypass Parmana, or call another execution system.
>
> If Parmana returns APPROVED and provides execution evidence, report the resulting execution state and evidence identifiers accurately. Do not claim success if the execution result is ambiguous or incomplete.
>
> Never expose secrets, API keys, connector credentials, or internal authorization tokens.

## Tool input contract

The authorization tool should accept structured inputs:

- `order_id`: string, required
- `transaction_id`: string, required
- `amount`: positive number, required
- `currency`: string, required; initial demo uses INR
- `reason`: string, required
- `refund_eligible`: boolean, required
- `manager_approved`: boolean, required
- `fraud_check_passed`: boolean, required

## Tool output contract

Return structured output containing at minimum:

- `status`: `APPROVED` or `DENIED`
- `executed`: boolean
- `state`
- `reason` when denied
- `authorization_id` when available
- `execution_id` when available
- `evidence` / trust-record identifiers when available

## Secrets

Configure only the credentials required to call Parmana, using Phinite environment variables/secrets:

- `PARMANA_API_URL`
- `PARMANA_API_KEY`
- `PARMANA_PRINCIPAL_ID`

Do NOT configure Paytm merchant credentials in this agent.
