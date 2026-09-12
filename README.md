# Parmana Phinite Agent

Autonomous AI commerce agent built on Phinite, with Parmana as the execution-authority layer.

## Principle

**AI can be intelligent without being in charge.**

The agent may understand a customer request and propose an action. It must not decide whether a consequential action is authorized. Parmana makes that decision.

## Initial use case

Customer refund through a live commerce/payment execution path.

```text
Customer
   ↓
Phinite Agent
   ↓
Refund Intent
   ↓
Parmana Authorization
   ├── DENIED → STOP
   └── APPROVED
          ↓
     Governed Execution
          ↓
     Paytm Connector
          ↓
     Paytm API
          ↓
     Execution Evidence
```

## Trust boundary

This repository contains the agent-side integration. It must not hold Paytm merchant credentials or call the Paytm connector directly. The agent calls Parmana and treats Parmana's decision as authoritative.

## Status

Phase 1: repository initialization.

Next: define the Phinite graph, refund tool contract, and Parmana `/execute` integration.
