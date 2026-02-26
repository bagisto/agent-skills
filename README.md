# bagisto/agent-skills

Agent skills for [Bagisto](https://bagisto.com) — a Laravel-based open-source e-commerce platform.

These skills provide domain-specific, reusable context for AI agents (Claude Code, Cursor, Windsurf, etc.) working inside a Bagisto codebase.

## Available Skills

### `pest-testing`

Tests applications using the Pest 3 PHP framework.

**Activates when:** writing tests, creating unit or feature tests, adding assertions, testing Livewire components, architecture testing, debugging test failures, working with datasets or mocking — or when the user mentions `test`, `spec`, `TDD`, `expects`, `assertion`, `coverage`, or needs to verify functionality works.

---

### `payment-method-development`

Payment gateway development in Bagisto.

**Activates when:** creating payment methods, integrating payment gateways like Stripe, PayPal, or any third-party payment processor — or when the user mentions `payment`, `payment gateway`, `payment method`, `Stripe`, `PayPal`, or needs to add a new payment option to the checkout.

---

## Install

Install all skills from this repo into your AI agent:

```bash
npx skills add bagisto/agent-skills
```

Install a specific skill only:

```bash
npx skills add bagisto/agent-skills --skill "pest-testing"
npx skills add bagisto/agent-skills --skill "payment-method-development"
```

Install for a specific agent:

```bash
npx skills add bagisto/agent-skills -a claude-code
npx skills add bagisto/agent-skills -a cursor
```

## Repository Structure

```
agent-skills/
├── skills/
│   ├── pest-testing/
│   │   └── SKILL.md
│   └── payment-method-development/
│       └── SKILL.md
├── AGENTS.md
└── README.md
```

Each skill folder contains a SKILL.md file with agent-readable instructions and a YAML frontmatter block that defines when the skill activates.
