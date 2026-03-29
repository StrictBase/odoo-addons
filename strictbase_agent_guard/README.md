# `strictbase_agent_guard`

## Guide

→ [Giving Your AI Agent a Seat in Odoo](https://strictbase.com/guides/odoo-agent-access.html) — StrictBase Guides

Odoo 19.0 Community Edition module for agent-mode outbound safety.

## Purpose

This module adds a small Odoo-side guardrail for broad agent access.

The design goal is:

- keep agent access broad and generic
- avoid a narrow hardcoded action catalog
- block client-facing outbound communication unless it is explicitly confirmed

This module is meant to complement:

- a broad non-superuser Odoo agent account
- JSON-2 access
- helper-side logging and execution flow

It is not meant to be a general policy engine.

## What It Guards

When `agent_mode` is enabled in the Odoo context, the module blocks these outbound paths unless a valid confirmation token is present:

- `mail.thread.message_post`
  - non-note comments
  - explicit outbound email recipients
  - external partner recipients
- `mail.compose.message.action_send_mail`
  - non-log sends
- `account.move.send.wizard.action_send_and_print`
  - invoice sends that include email
- `account.move.send.batch.wizard.action_send_and_print`
  - batch invoice sends that include email

The guard raises an Odoo `UserError` with the marker:

```text
AGENT_CONFIRMATION_REQUIRED
```

## Confirmation Tokens

The module includes a small model:

- `strictbase.agent.confirmation`

It issues:

- short-lived
- scoped
- one-time

confirmation tokens tied to:

- user
- model
- method
- record ids

These are intended for agent workflows that need explicit human approval before an outbound action is retried.

Token issuance is restricted to users in the module's `Agent Confirmation Approver` group. The agent account itself should not be in that group.

## Trust Boundary

This module protects the Odoo-side confirmation boundary only if the agent cannot also access approver credentials outside Odoo.

In practice:

- the ordinary agent user must not be in `Agent Confirmation Approver`
- the approver API key must be held separately from the agent API key
- the approver key should only be supplied by a trusted human-controlled flow

If a fully trusted host-level agent can read and use the approver key directly, then it can still authorize outbound actions at the host level even though the Odoo-side model restriction is correct.

## Runtime Contract

The guard is only active when the Odoo context contains:

- `agent_mode = True`

The confirmation path uses:

- `agent_confirmation_token`

Without `agent_mode`, ordinary human Odoo usage is unaffected.

## Installation

This module lives in the StrictBase addons repo and is expected to be available in the Odoo `addons_path`.

Example install:

```bash
python3 odoo-bin \
  -c <odoo.conf> \
  -d <db> \
  -i strictbase_agent_guard \
  --stop-after-init \
  --logfile=""
```

Example update:

```bash
python3 odoo-bin \
  -c <odoo.conf> \
  -d <db> \
  -u strictbase_agent_guard \
  --stop-after-init \
  --logfile=""
```

## Local Development

This is the one addon README that intentionally includes a local-development flow.
Developers working on the agent guard are expected to have a local Odoo installation,
so the example below is developer-oriented and should be adapted to the local checkout,
config path, database name, and service names in use.

Typical local update flow:

```bash
systemctl --user stop <local-odoo-service>
python3 odoo-bin \
  -c <local-odoo.conf> \
  -d <local-db> \
  -u strictbase_agent_guard \
  --stop-after-init \
  --logfile=""
systemctl --user start <local-odoo-service>
```

## Tests

Test coverage is in:

- `tests/test_agent_guard.py`

The tests cover the main expected behavior:

- outbound comment blocked in agent mode
- internal note allowed
- mail composer send blocked
- invoice send blocked
- scoped confirmation token allows exactly one approved retry

## Intended Use

This module is part of a broader StrictBase agent-access setup.

The intended pattern is:

1. agent uses broad JSON-2 access
2. agent works normally for internal Odoo actions
3. if an outbound client-facing action is attempted in agent mode, Odoo blocks it
4. the higher-level agent flow asks for human confirmation
5. the action is retried with a valid scoped token

That keeps the hard safety boundary in Odoo for the highest-risk class of action without turning Odoo into a heavy policy layer.
