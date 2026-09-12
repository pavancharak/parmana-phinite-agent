# Architecture

## System boundary

Phinite owns agent reasoning, orchestration, conversation state, and tool invocation.

Parmana owns authorization and governed execution.

The Paytm connector owns deterministic communication with Paytm and is isolated from this agent repository.

## Flow

```text
Customer
  |
  v
Phinite Agent Graph
  |
  | 1. understand request
  | 2. produce structured RefundIntent
  v
Parmana Refund Tool
  |
  | POST /execute
  v
Parmana
  |
  +---- DENIED ----> return decision -> STOP
  |
  +---- APPROVED ---> governed execution
                           |
                           v
                    Paytm Connector
                           |
                           v
                       Paytm API
                           |
                           v
                   Trust / Audit Evidence
```

## Non-negotiable rules

1. The LLM is not an authorization authority.
2. The LLM must never fabricate `refundEligible`, `managerApproved`, or `fraudCheckPassed`.
3. Structured business signals must come from a trusted upstream source, session variable, or authoritative tool.
4. The agent must not call the Paytm connector directly.
5. Paytm credentials must never be stored in this repository or exposed to the Phinite agent.
6. A Parmana denial is terminal for that execution attempt.
7. An approval is the only path that may proceed to governed execution.
8. Ambiguous execution outcomes must not be converted into a success claim.
9. Every consequential action must remain traceable to the originating request and Parmana decision.
