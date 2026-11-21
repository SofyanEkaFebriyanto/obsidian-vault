#!/usr/bin/env node
/**
 * Probe a page's response contract.
 *
 * Dumps every response the page produces — URL, method, status, content-type,
 * top-level JSON keys — plus the distinct URL patterns with the host
 * normalised. Build your driver's response filter and your classifier's key
 * list from this output instead of guessing.
 *
 * A too-narrow filter makes every attempt report "unknown" and looks like
 * "the app is broken" rather than "my regex is wrong".
 *
 * Usage:
 *   node probe_page_responses.mjs <url> [waitMs]
 *
 * Requires: playwright-core + a system Chrome, e.g.
 *   npm i playwright-core
 *   node probe_page_responses.mjs https://example.com 5000
 */

import { chromium } from 'playwright-core'

const url = process.argv[2]
const waitMs = Number(process.argv[3] || 5000)
const CHROME = process.env.CHROME_PATH || '/usr/bin/google-chrome'

if (!url) {
  console.error('usage: node probe_page_responses.mjs <url> [waitMs]')
  process.exit(1)
}

/** Replace the host with a placeholder so URL variants collapse into patterns. */
function normalize(u) {
  try {
    const url = new URL(u)
    return url.pathname.replace(/\d{4,}/g, ':id').replace(/[a-z0-9]{16,}/gi, ':hash')
  } catch {
    return u
  }
}

function topLevelKeys(body) {
  if (!body || typeof body !== 'object') return null
  return Object.keys(body).slice(0, 20)
}

function preview(body) {
  if (body === null || body === undefined) return ''
  if (typeof body === 'string') return body.slice(0, 120).replace(/\s+/g, ' ')
  try {
    return JSON.stringify(body).slice(0, 200)
  } catch {
    return '[unserializable]'
  }
}

const browser = await chromium.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
})

const context = await browser.newContext({ ignoreHTTPSErrors: true })
const page = await context.newPage()

const rows = []
const patterns = new Map()

page.on('response', async (res) => {
  const contentType = res.headers()['content-type'] || ''
  let body = null
  let parseError = null
  try {
    if (contentType.includes('json')) body = await res.json()
    else body = (await res.text().catch(() => '')).slice(0, 400)
  } catch (e) {
    parseError = e.message
  }

  const pat = normalize(res.url())
  if (!patterns.has(pat)) {
    patterns.set(pat, { count: 0, status: res.status(), contentType, keys: topLevelKeys(body) })
  }
  patterns.get(pat).count++

  rows.push({
    method: res.request().method(),
    status: res.status(),
    contentType: contentType.split(';')[0] || '(none)',
    url: res.url().slice(0, 160),
    pattern: pat,
    keys: topLevelKeys(body),
    parseError,
    preview: preview(body),
  })
})

page.on('requestfailed', (req) => {
  rows.push({
    method: req.method(),
    status: 'FAILED',
    contentType: '',
    url: req.url().slice(0, 160),
    pattern: normalize(req.url()),
    keys: null,
    parseError: req.failure()?.errorText || '',
    preview: '',
  })
})

console.log(`# probing ${url} (waiting ${waitMs}ms)\n`)

try {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 })
  await page.waitForTimeout(waitMs)
} catch (e) {
  console.error(`navigation failed: ${e.message}`)
}

console.log('## DISTINCT URL PATTERNS (host normalised)')
console.log('count | status | content-type | top-level JSON keys | pattern')
for (const [pat, info] of patterns) {
  console.log(
    `${String(info.count).padStart(5)} | ${String(info.status).padStart(6)} | ` +
      `${(info.contentType || '(none)').slice(0, 30).padEnd(30)} | ` +
      `${(info.keys ? info.keys.join(',') : '-').slice(0, 60).padEnd(60)} | ${pat}`,
  )
}

console.log('\n## ALL RESPONSES')
for (const r of rows) {
  console.log(
    `${r.method} ${r.status} [${r.contentType}] ${r.url}\n` +
      `    pattern: ${r.pattern}\n` +
      (r.keys ? `    keys:    ${r.keys.join(', ')}\n` : '') +
      (r.parseError ? `    error:   ${r.parseError}\n` : '') +
      (r.preview ? `    body:    ${r.preview}\n` : ''),
  )
}

console.log(
  `\n# ${rows.length} responses, ${patterns.size} distinct patterns.\n` +
    '# Build your filter from the patterns above. The ones carrying a\n' +
    '# JSON body with payment/result keys are your verdict sources.\n' +
    '# Any pattern whose body is JSON but was NOT classified is a filter bug.',
)

await browser.close()
