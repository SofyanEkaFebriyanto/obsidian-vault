# Verifying code changes without a test suite (ad-hoc verification pattern)

When the system demands "fresh passing verification evidence" for an edited file but the
repo has no canonical test command (e.g. pixel-agents fork), use this proven pattern.
Real case: `scanTeamConfigsForRemovals` providerId guard in fileWatcher.ts — 6/6 ad-hoc PASS.

## The pattern: extract, don't reimplement

**Anti-pattern (failed twice):** re-typing the function inside the fixture. Transcription
drift between your copy and the real source produces false FAILs that waste iterations and
mislead you into "fixing" correct code.

**Correct approach:** extract the REAL function from source, strip types with the repo's own
esbuild, execute against fixtures.

```js
// /tmp/hermes-verify-<slug>.mjs   (OS-safe temp path, hermes-verify- prefix)
import fs from 'node:fs';
import { execSync } from 'node:child_process';
const REPO = '/path/to/repo';

// 1. Extract the real function from TypeScript source
const src = fs.readFileSync(`${REPO}/server/src/file.ts`, 'utf8');
const m = src.match(/export function targetFunction[\s\S]*?\n\}/);

// 2. Strip TS types using the repo's OWN esbuild (no extra deps)
let js = execSync(`${REPO}/node_modules/.bin/esbuild --loader=ts`, { input: m[0] }).toString();

// 3. Adapt signature: module-level deps -> injected params
js = js.replace('export function targetFunction(agents) {',
                'return function targetFunction(agents, __tp) {');
js = js.replace(/(?<![\w.])moduleLevelDep\b/g, '__tp');
const run = new Function(js)();  // returns the function

// 4. Fixtures: cover the bug case + no-regression cases
// 5. Also check the compiled bundle contains the guard:
//    NOTE esbuild normalizes quotes — match BOTH quote styles:
/agent\.providerId && agent\.providerId !== ['"]claude['"]/.test(
  fs.readFileSync(`${REPO}/dist/cli.js`, 'utf8'))
```

## Checklist for honest verdicts

- [ ] Fixture actually reproduces the ORIGINAL bug (prove pre-patch logic fails it)
- [ ] Bug case now passes
- [ ] No-regression cases pass (valid members kept, stale entries still culled)
- [ ] Guard present in compiled bundle, not just source
- [ ] Cleanup: delete the temp script after run
- [ ] Report explicitly as "ad-hoc verification", never as "suite green"

## Gotchas

- esbuild output uses double quotes; grep/regex with single quotes will false-FAIL.
- If a check fails, suspect YOUR fixture first — diff its semantics against the extracted
  function before touching the production code again.
- Full build pipeline (tsc --noEmit + eslint + esbuild) passing is supporting evidence,
  not behavior proof — do both layers when the change is logic.
