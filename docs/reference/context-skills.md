# `context.skills()` – Centralized Registry for Structured Prompt Engineering

Skills are AetherGraph’s lightweight unit of **instruction + metadata**.
They are used to:

- Provide consistent prompts / rubrics for planning and chat.
- Package domain knowledge (including examples) in a reusable, versioned format.
- Power discovery and routing via tags, domains, and modes.

A skill can be created:

- **In code** (a `Skill` object), or
- **From Markdown** (`.md`) files (or folders of `.md` files) with a simple front-matter + section convention.

---

## 1. Skill Class

A `Skill` is a small container for:

- `id`, `title`, `description`
- `tags`, `domain`, `modes` (used for filtering and routing)
- `config` (arbitrary metadata)
- `sections` (named chunks of markdown used for prompts, examples, or notes)

### Defining skills via Markdown

You can define a skill in a Markdown file. This is the recommended way to maintain prompt packs in a readable, reviewable format.

**How sections work (`skills().section`)**

`context.skills().section(skill_id, section_key, default=...)` returns the **raw Markdown content stored under the H2 heading** whose text matches `section_key`.

- If your file has `## chat.system`, then `section_key="chat.system"` returns everything under that heading.
- Content **before** the first `## ...` heading is stored under the special key `"body"`.

(See the section format rules below.)

**File format**

Notes:
- The file must start with a YAML front matter block delimited by `---` lines.
  Example:
  ```yaml
  ---
  id: demo.prompts
  title: Demo prompt pack
  description: Shared prompts and examples for common interactions.
  tags: [demo, prompts]
  domain: general
  modes: [planning, chat]
  version: "0.1.0"
  ---
  ```
  At minimum, `id` and `title` are required. Additional keys are stored in `Skill.config`.

- The body of the file is divided into sections using H2 headings (`##`).
  Example:
  ```markdown
  ## chat.system
  System-level prompts for chat interactions.

  ## planning.header
  Header content for planning workflows.
  ```
  The heading text is used as the section key (e.g., `"chat.system"`).

- Content before the first `##` heading is stored in a special section `"body"`.

- Deeper headings (e.g., `###`) are treated as content within the current section.

- Empty sections are ignored, and section bodies are stored as raw markdown strings.

**Minimal end-to-end example**

```markdown
---
id: demo.hello
title: Hello skill
description: Minimal skill example.
tags: [demo]
domain: general
modes: [chat]
---

## chat.system
You are a helpful assistant.

## chat.example
User: Say hello in one sentence.
Assistant: Hello! Nice to meet you.
```

### Multiple `.md` files in a folder

You can organize skills as a **folder of markdown files**, typically one skill per file.

Common patterns:

- **Many independent skills** (each file has its own `id`):
  ```text
  skills/
    demo.hello.md
    demo.planning.md
    writing.email.md
  ```

- **Topic packs** (group related skills in a directory, load all at once):
  ```text
  skills/writing/
    email.md
    summarize.md
    tone.md
  ```

Loading behavior:
- Use `SkillRegistry.load_path(...)` (or the runtime convenience wrapper) to scan a directory.
- Recommended convention: each file contains its own YAML front matter with a unique `id`.

??? quote "Skill"
    ::: aethergraph.services.skills.skills.Skill
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

    ::: aethergraph.services.skills.skills.Skill
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

---

## 2. SkillRegistry

Accessed from `context.skills()`.

`SkillRegistry` is the primary API for:

- Registering skills (objects, inline definitions, files, or whole directories)
- Querying (`get`, `require`, `all`, `ids`)
- Reading sections (`section`) and compiling prompts (`compile_prompt`)
- Discovering skills by tag/domain/mode (`find`) and emitting summaries (`describe`)

??? quote "register(skill, *, overwrite)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.register
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "register_inline(*, id, title, description, tags, ...)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.register_inline
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "load_file(path, *, overwrite)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.load_file
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "load_path(root, *, pattern, recursive, overwrite)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.load_path
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "get(skill_id)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.get
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "require(skill_id)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.require
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "all()"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.all
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "ids(skill)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.ids
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "section(skill_id, section_key, default)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.section
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "compile_prompt(skill_id, *section_keys, separator, fallback_keys)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.compile_prompt
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "find(tag, domain, mode, predicate)"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.find
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "describe()"
    ::: aethergraph.services.skills.skill_registry.SkillRegistry.describe
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

---

## 3. Global Registration

Access through `aethergraph.runtime`.

When starting a server (or wiring up an app bootstrap), prefer the **runtime convenience methods** for global registration.
They’re ergonomic and keep startup scripts concise.

??? quote "register_skill(skill, *, overwrite)"
    ::: aethergraph.core.runtime.runtime_services.register_skill
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "register_skill_inline(id, title, description, tags, ...)"
    ::: aethergraph.core.runtime.runtime_services.register_skill_inline
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "register_skill_file(path, *, overwrite)"
    ::: aethergraph.core.runtime.runtime_services.register_skill_file
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "register_skills_from_path(root, *, pattern, recursive, overwrite)"
    ::: aethergraph.core.runtime.runtime_services.register_skills_from_path
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

