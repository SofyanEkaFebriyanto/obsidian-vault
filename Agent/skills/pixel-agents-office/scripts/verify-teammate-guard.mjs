#!/usr/bin/env node
// Ad-hoc verification for the providerId guard in scanTeamConfigsForRemovals
// (pixel-agents server/src/fileWatcher.ts).
// Pattern: extract the REAL function from TS source, strip types with the repo's
// esbuild, execute against fixtures. No re-implementation = no transcription drift.
// Usage: node verify-teammate-guard.mjs   (exit 0 = all pass)
import fs from 'node:fs';
import { execSync } from 'node:child_process';

const REPO = process.env.PA_REPO || `${process.env.HOME}/hermes-agent-pixel/pixel-agents`;
const results = [];
const check = (name, ok, detail='') => { results.push([name, ok]); console.log(`${ok ? 'PASS' : 'FAIL'}: ${name} ${detail}`); };

const src = fs.readFileSync(`${REPO}/server/src/fileWatcher.ts`, 'utf8');
const m = src.match(/export function scanTeamConfigsForRemovals[\s\S]*?\n\}/);
check('function found in source', !!m);
if (!m) process.exit(1);

const esbuild = `${REPO}/node_modules/.bin/esbuild`;
let js = execSync(`${esbuild} --loader=ts`, { input: m[0] }).toString();
js = js.replace('export function scanTeamConfigsForRemovals(agents) {',
                'return function scanTeamConfigsForRemovals(agents, __tp) {');
js = js.replace(/(?<![\w.])teamProvider\b/g, '__tp'); // module-level provider -> injected param
const run = new Function(js)();

const dissolved = { getTeamMembers: () => null }; // ~/.claude/teams/<t>/config.json missing
const healthy   = { getTeamMembers: (t) => t === 'Alpha' ? new Set(['worker-a']) : new Set() };
const agents = new Map([
  [3, { leadAgentId:1, teamName:'Hermes', agentName:'kenfa-backend',  providerId:'hermes', teamUsesTmux:false }],
  [4, { leadAgentId:1, teamName:'Hermes', agentName:'kenfa-frontend', providerId:'hermes', teamUsesTmux:false }],
  [5, { leadAgentId:2, teamName:'Alpha',  agentName:'worker-a',       providerId:'claude', teamUsesTmux:false }],
]);

const rDissolved = run(agents, dissolved);
const rHealthy   = run(agents, healthy);
const rStale     = run(new Map([[9, { leadAgentId:2, teamName:'Alpha', agentName:'ghost', providerId:'claude', teamUsesTmux:false }]]), healthy);

check('dissolved team: Hermes teammates spared (the bug)', !rDissolved.includes(3) && !rDissolved.includes(4), `removed=[${rDissolved}]`);
check('dissolved team: claude teammate culled when its own team dissolved', rDissolved.includes(5));
check('healthy scan keeps valid members', rHealthy.length === 0);
check('stale claude teammate still culled (no false-negative regression)', JSON.stringify(rStale) === '[9]');

// Compiled bundle contains the guard (quote-agnostic — esbuild normalizes quotes)
const bundle = fs.readFileSync(`${REPO}/dist/cli.js`, 'utf8');
check('guard compiled into dist/cli.js', /agent\.providerId && agent\.providerId !== ['"]claude['"]/.test(bundle));

const allPass = results.every(([, ok]) => ok);
console.log(`\nAD-HOC VERIFICATION: ${allPass ? 'ALL PASS' : 'FAILURES PRESENT'} (${results.filter(r=>r[1]).length}/${results.length})`);
process.exit(allPass ? 0 : 1);
