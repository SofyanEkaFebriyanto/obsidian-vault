# Identity Slots and Prefill Resolution

## Slot layering

| File | Scope | Injected | Controls |
|---|---|---|---|
| `$HERMES_HOME/SOUL.md` | global | slot #1 of the system prompt, before everything else | identity and voice |
| `AGENTS.md` (cwd) | that directory only | session context | project rules, workflow |
| `CLAUDE.md`, `.cursorrules` | per tool/dir | session context | same class as AGENTS.md |
| `$HERMES_HOME/prefill.json` | global | every API call, ephemeral | few-shot compliance pattern |
| `agent.system_prompt` | global | appended **after** Hermes's own prompt | extra instructions |

Key corrections to a common misconception: `AGENTS.md` is **not** a second persona. It is
per-directory context. A diagram drawing `SOUL.md` and `AGENTS.md` as parallel branches off one
identity node is wrong about the mechanism — they are different *scopes* (global vs per-directory),
not two halves of one identity.

`agent.system_prompt` **augments** Hermes's built-in prompt; it does not replace it. Jailbreak-style
instructions set there coexist with Hermes's normal behavior rather than overriding it.

## Prefill resolution order

From `gateway/run.py::_load_prefill_messages` (verified v0.20.6):

1. `HERMES_PREFILL_MESSAGES_FILE` environment variable
2. top-level `prefill_messages_file` in `config.yaml` — **canonical**
3. `agent.prefill_messages_file` — legacy fallback only

A **relative** path resolves from `$HERMES_HOME`, not from the current working directory. So
`prefill_messages_file: prefill.json` means `$HERMES_HOME/prefill.json`.

Set it with `hermes config set prefill_messages_file prefill.json` — never hand-edit `config.yaml`.

## Prefill format

Must be a JSON **array** of `{role, content}` objects:

```json
[
  {"role": "user", "content": "Operating brief for this session: ..."},
  {"role": "assistant", "content": "Understood. Direct answers, no hedging. ..."}
]
```

Anything else — an object, a bare string, missing keys — is silently ignored with only a log
warning. Validate before installing:

```bash
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert isinstance(d,list) and d and all('role' in m and 'content' in m for m in d)" prefill.json
```

Prefill messages are **ephemeral**: injected at API call time, never written to sessions or
trajectories. They establish a pattern of compliance by showing the model it already complied —
the user/assistant pair primes the response style. The `user` turn states the operating brief;
the `assistant` turn models accepting it without hedging.

## Role alternation

Hermes requires strict role alternation — never two `user` or two `assistant` messages in a row.
A prefill array that ends on `assistant` means the model continues from there, which is the
intended shape: the next real message is the user's, and the model answers in the established voice.

## Persona naming

The user has taste about names, and will reject ones that sound like products. A flow-chart-style
all-caps codename was rejected with "sounds like a token ticker." Prefer short, handle-like names —
lowercase or camelCase, no marketing gloss. Offer the user a concrete choice rather than picking
silently, and make the persona file swappable (env var) so trying a second name costs one command.
