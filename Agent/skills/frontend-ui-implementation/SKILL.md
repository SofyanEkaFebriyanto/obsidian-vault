---
name: frontend-ui-implementation
description: Build and verify frontend UI features in an existing app without overreaching into backend/server work.
tags: [frontend, ui, alpine, blade, localstorage, verification]
---

# Frontend UI Implementation

Use when the user asks to implement or continue a frontend-facing feature: cart drawer, product UI, filters, checkout shell, responsive polish, interactive components, Blade/Alpine/Tailwind UI, or similar.

## Core rules

1. Scope first. If user says "frontend only", do not create controllers, services, routes, migrations, API endpoints, or DB changes. If you already started backend work, revert/delete it before proceeding.
2. Read existing UI structure before editing: layout, partials, page view, JS entrypoint, CSS/theme, and relevant data passed from server-rendered templates.
3. Reuse existing patterns: Blade partials, Alpine components/stores, Tailwind tokens, theme colors, helper formatting already present.
4. Keep UI state client-side unless user asked for persistence/server integration. Good prototype stores: Alpine store + `localStorage` for browser-persistent cart-like state; in-memory Alpine for ephemeral panels/forms.
5. Do not overbuild hidden backend plumbing. Frontend placeholder buttons are allowed if they are clearly UI-only and do not imply real checkout/payment/order persistence.

## Alpine/Blade pattern

1. Put reusable cross-page state in `resources/js/app.js` as an Alpine store/component.
2. Put reusable UI panels in `resources/views/partials/*.blade.php`, then include from main layout.
3. Wire header/nav buttons to global store actions, not ad-hoc DOM listeners.
4. For PDP/cart UI, pass only needed server data into Alpine via `@js(...)`:
   - product id/name/slug/url/image
   - variant id/size/price/stock/active
5. Key cart items by product + variant (`productId:variantId`) so same product with different sizes stays distinct.
6. For currency in PHP-rendered content, use project helper. For JS-only previews, use `Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })` and treat it as frontend-only display.

## Verification

For visual/creative UI, avoid heavy test/lint churn until user likes direction or before commit. Still do focused smoke checks when code changed:

1. Run project build through environment that owns dependencies (often Docker container) if host permissions fail.
2. Browser-smoke key interactions: open panel, empty state, choose option, add item, qty +/-/remove, subtotal/badge update, no console errors.
3. If no canonical test/lint/build command is detected by harness, create a temporary ad-hoc script under `/tmp` using prefix `hermes-verify-`, run targeted checks against changed behavior, then delete it. Report it explicitly as ad-hoc verification, not full suite green.

## References

- `references/kenfa-cart-checkout-frontend.md` — concrete Laravel Blade + Alpine pattern for frontend-only cart drawer and checkout shell, including scope pitfall, localStorage store, route placement before catch-all, and ad-hoc verification.
- `references/kenfa-hero-banner-fallback.md` — frontend-only hero/banner pattern when seeded banner image paths are missing: derive product image fallback from already-passed collections, always render image, and verify with build + ad-hoc script + visual smoke.

## Cross-nested Alpine event pattern (addressPicker → checkoutPage)

When an inner Alpine component (`addressPicker`, rendered inside a `div.contents` with `x-data`) needs to propagate a value change to an outer Alpine component (`checkoutPage` on the enclosing `<form>`), use `$dispatch` + `addEventListener`:

Inner component dispatches:
```js
this.$dispatch('postal-code-changed', { code: this.postalCode });
// also: this.$watch('postalCode', (val) => this.$dispatch('postal-code-changed', { code: val }));
```

Outer component listens in `init()`:
```js
this.$el.addEventListener('postal-code-changed', (e) => {
    this.shipping.postalCode = e.detail.code;
});
```

Why not `$watch` on the outer? The outer component can't `$watch` a property that belongs to a different `x-data` scope. `$dispatch` bubbles up the DOM naturally. The outer's `$el` is the `<form>` element, which is an ancestor of the inner `div.contents`, so the event reaches it. This pattern was used for kode pos dropdown → ongkir rate fetch (shipping.postalCode triggers scheduleRates() which is `$watch`'d in checkoutPage).

## Pitfalls

- Do not answer "done" after only static edits; exercise interaction if browser/server is available.
- Do not silently keep backend files when user corrects scope to frontend-only.
- Do not create backend scaffolding when user asks frontend-first/frontend-only; if already created, delete it before proceeding.
- If a UI mockup expects imagery but seeded/static assets are missing, prefer a graceful frontend fallback from data already available in the view (e.g. product images) before touching seeders, storage, controllers, or DB.
- Do not call frontend-local cart/order/payment "real" checkout. It is UI state until backend integration exists.
- Watch unrelated dirty files in `git status`; mention them, do not fix them unless asked.
- **Dead Alpine `@click` button in a fixed bottom-nav (or any fixed bar) = child elements intercepting the click, not broken JS.** Symptom: some tabs (plain `<a href>`) work but `<button @click="...">` tabs don't respond on tap. Cause: the SVG icon / label `<span>` sit on top of the button and swallow the tap target, and/or the bar has no stacking context above page content. Fix (apply to the whole bar): give the bar `relative z-50`, the container `relative z-10`, each tab `relative z-10`, and add `pointer-events-none` to every child that shouldn't capture clicks (icon `svg`, label `span`, and the notification `badge` span). Verify by grepping the rendered HTML for `pointer-events-none` on the icon/label/badge. This is a CSS hit-testing issue — `node --check` on app.js will pass and mislead you.
