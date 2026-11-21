# Designing a mock that actually exercises a driver

A mock is not "a page that returns 200". It is a **branch generator**: it must
be able to produce every verdict the driver can emit, so the driver's decision
table is exercised without touching a live target.

## The verdict contract

Decide this before writing the mock, and make both sides agree:

| state | meaning | exit code contribution |
|---|---|---|
| `hit` | the operation succeeded | `0` |
| `decline` | the operation failed for a *business* reason (card declined, insufficient funds) | `2` |
| `unknown` | no verdict — timeout, unparseable body, endpoint not observed | `2` |
| setup error | could not reach the form at all | `1` |

`unknown` must be a first-class state, distinct from `decline`. Collapsing them
is how a driver ends up reporting "declined" for a network timeout, which then
looks like the target rejecting valid input.

## Drive the verdict from the input

Make the fixture select the branch. A card number's last digits are the
cheapest discriminator:

```js
if (number.endsWith('0000')) -> { status: 'succeeded', paid: true }        // hit
if (number.endsWith('9999')) -> { error: { code: 'card_declined', decline_code: 'generic_decline' } }
if (number.endsWith('8888')) -> { error: { code: 'expired_session', decline_code: 'expired_session' } }
                                  // dead session -> driver must STOP, not continue
return                     -> { error: { decline_code: 'insufficient_funds' } }
```

Then the fixture file drives the matrix:

```
4111111111110000|12|30|123     -> hit
5555555555559999|12|30|123     -> generic_decline
4000000000000002|12|30|123     -> insufficient_funds
4444444444448888|12|30|123     -> expired_session (run must stop after 1 attempt)
```

One file, four branches, one command.

## Response-shape fidelity beats realism

The mock does **not** need to look like the target. It needs to return bodies
with the **same keys the classifier reads**. If the classifier looks for
`payment_intent.status === 'succeeded'`, the mock must return that nesting
depth — not a flat `{success: true}`.

Copy the real key names and nesting from the live response (probe it — see
`scripts/probe_page_responses.mjs`). Match:

- key names and nesting depth
- the field the decline code lives in (`error.decline_code` vs top-level
  `decline_code` vs `outcome.reason`)
- the human-readable message text, if the classifier maps messages → codes

A mock that returns a different shape than the classifier expects passes its
own tests and fails in production. That is the single most common mock defect.

## The endpoint must look like the real one

Your driver's response filter is a URL regex. If the mock posts to
`/api/stripe/v1/payment_intents` and the filter is `/api\/stripe\//i`, the
filter is exercised; if the mock posts to `/pay` and the filter only matches
`payment_intents`, the filter is **not** exercised and every attempt returns
`unknown` — with the driver looking correct.

Mirror the real path shape in the mock. When the filter is too narrow, the
symptom is uniformly `unknown`, which reads as "the target is broken" rather
than "my regex is wrong". Two defenses:

- build the filter from probed real output, not from a guess;
- on `unknown`, print the responses that were observed but not classified.

## Exercise the hard surface: iframes

If the real target puts fields in iframes (Stripe Elements, hCaptcha, any
embedded widget), the mock must too — otherwise the iframe code path ships
unverified.

A `data:` URL iframe is the cheapest faithful stand-in:

```js
const IFRAME_SRC = `data:text/html,${encodeURIComponent(
  `<!doctype html><body><input id="n" aria-label="Card number"></body></html>`
)}`
```

Two traps, both of which will bite:

1. **The parent cannot read the child's input** — `contentDocument` is `null`
   cross-origin, even for a `data:` URL. Relay the value with `postMessage`:
   the child posts on `input`, the parent stores it, the submit handler reads
   the stored value. This is also how a real Elements iframe behaves, so the
   mock is more faithful than a same-origin shortcut.
2. **The driver must reach the iframe via `frameLocator`**, e.g.
   `page.frameLocator('iframe[title*="card number" i]').locator('input')`.
   Give the mock iframes `title` attributes that match the real ones
   (`Secure card number input`, …) so the driver's title-based selector is the
   thing under test.

Two mock files is the right shape: one plain-DOM (the easy path) and one
iframe-based (the hard path). Assert on the *surface* as well as the verdict:

```
ok   card typed into cross-origin iframes   <- log says "filled 3 iframe fields"
ok   hit detected through iframes
```

## Make the dead-session path testable

Real sessions expire mid-run. The driver must detect that and **stop**, not
burn the remaining attempts against a dead session. Give the mock a
distinctive decline code for it (`expired_session`) and assert the run
performed **one** attempt, not N.

This is a branch that is nearly impossible to hit live on demand, and nearly
impossible to notice if broken — you just see "attempts stopped early" with no
error. In a mock it is one line.

## The mock's own endpoint

The mock's response endpoint should mirror the real request too: same method,
same content-type, same body encoding (form-encoded vs JSON). If the real page
posts `application/x-www-form-urlencoded` and your mock posts JSON, any
body-rewriting logic in the driver is untested.

## Checklist

- [ ] Verdict contract agreed: `hit` / `decline` / `unknown` / setup-error
- [ ] Fixture file selects every branch (success, each decline code, dead session)
- [ ] Response bodies use the real key names and nesting depth
- [ ] Endpoint path + method + content-type mirror the real request
- [ ] A second mock covers the iframe surface if the real target uses one
- [ ] Cross-origin read uses `postMessage`, not `contentDocument`
- [ ] Dead-session branch asserts the run stopped early
- [ ] `unknown` (timeout) is asserted as its own state, not folded into decline
- [ ] Test asserts the fill surface, not just the verdict
