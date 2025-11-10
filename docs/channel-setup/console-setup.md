# Console Channel Overview

The **console channel** is the simplest built-in channel in AetherGraph. It prints messages to your terminal and, when possible, reads replies directly from standard input.

It is the default channel used when you don’t specify any other channel.

---

## Channel key

* Default channel key: `console:stdin`

* If you call:

  ```python
  await context.channel().send_text("Hello from AetherGraph")
  ```

  and you haven’t overridden the default channel, AetherGraph will use the console channel (i.e., `console:stdin`).

* You can also reference it explicitly:

  ```python
  chan = context.channel("console:stdin")
  await chan.send_text("This goes to the terminal")
  ```

---

## Capabilities

The console channel supports:

* **Text output** – plain messages printed to the terminal.
* **Input** – reading user input from standard input for `ask_*` methods.
* **Buttons/approvals** – `ask_approval` prompts are rendered as numbered options; you reply by typing a number or label.

Internally, the adapter declares:

```python
capabilities = {"text", "input", "buttons"}
```

---

## How `send_text` behaves

When you call:

```python
await context.channel().send_text("Hello 👋")
```

AetherGraph:

* Prints a line like:

  ```text
  [console] agent.message :: Hello 👋
  ```

* Returns immediately; there is no waiting or continuation involved.

This makes the console channel ideal for quick debugging, demos, and local experiments.

---

## How `ask_*` behaves

When you call `ask_text` or `ask_approval` on the console channel, AetherGraph will:

* Print a prompt to the terminal.
* Block briefly while it reads a line from `stdin` (via `sys.stdin.readline` in a background executor).
* Use that line as the response and resume your graph inline.

For example:

```python
name = await context.channel().ask_text("What is your name?")
await context.channel().send_text(f"Nice to meet you, {name}!")
```

This typically behaves with **no asynchronous wait** in the sense of external channels: everything happens in your local terminal session.

> Note: In non-interactive environments (e.g., no `stdin`, or CI), the console adapter may not be able to capture input. In that case, it will fall back to persisting a real continuation so the run can be resumed later. For normal local use in a terminal, `ask_*` works inline and does not require any external channel setup.
