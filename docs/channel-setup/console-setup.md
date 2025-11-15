# Console Channel Setup

The **console channel** is the simplest built‑in channel in AetherGraph. It prints messages to your terminal and, when possible, reads replies from standard input.

✅ **No setup required** — enabled by default.

🖥️ **Default key:** `console:stdin`

---

## Usage

```python
# Default: uses console if no other channel is configured
await context.channel().send_text("Hello from AetherGraph 👋")

# Explicit reference
chan = context.channel("console:stdin")
await chan.send_text("This goes to the terminal")
```

---

## Capabilities

* **Text output** (printed to terminal)
* **Input** via `ask_text`
* **Buttons/approvals** via `ask_approval` (rendered as numbered options)

Internally:

```python
capabilities = {"text", "input", "buttons"}
```

---

## `send_text`

```python
await context.channel().send_text("Hello 👋")
```

Prints a line like:

```
[console] agent.message :: Hello 👋
```

Returns immediately (no continuation).

---

## `ask_*`

```python
name = await context.channel().ask_text("What is your name?")
await context.channel().send_text(f"Nice to meet you, {name}!")
```

Prompts on the terminal, reads a line from **stdin**, and resumes inline (no external wait).

> **Notes:** In non‑interactive environments (CI, no stdin), input may not be available; the runtime persists a continuation for consistency, but does not allow resumption. For normal local terminals, `ask_*` works inline without extra config.
