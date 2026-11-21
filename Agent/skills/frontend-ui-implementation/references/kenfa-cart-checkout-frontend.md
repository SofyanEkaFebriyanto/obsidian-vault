# Kenfa cart + checkout frontend-only pattern

Context: Laravel Blade + Alpine + Tailwind storefront where user explicitly wanted frontend-only cart/checkout and corrected scope after backend service creation began.

## Durable lessons

- If user says focus frontend, do not add controllers/services/migrations/API routes. If backend work already started, remove it immediately and continue client-side.
- For guest-cart prototypes, use Alpine global store in `resources/js/app.js` + `localStorage` key such as `kenfa_cart`.
- Put drawer/panels in Blade partials and include from `layouts/app.blade.php` so header and pages share one cart state.
- Header cart badge should bind directly to `$store.cart.count`; cart button should call `$store.cart.toggle()`.
- PDP add-to-cart can pass minimal server data into Alpine via `@js(...)`: product id/name/slug/url/image and variant id/size/price/stock/active.
- Key cart lines by `productId:variantId`; same product different size must remain separate.
- Checkout shell can be `Route::view('/checkout', 'checkout')` placed before broad category catch-all routes. Keep submit button as dummy/toast when backend scope is excluded.
- Cart drawer checkout CTA should link to `route('checkout')`, not fake-submit inside drawer.
- Match project design doc tokens: navy primary, bg-main, white cards, Inter, uppercase bold headings, generous whitespace.

## Verification pattern

- Run build inside Docker if host `node_modules` permissions fail: `docker compose exec -T app npm run build`.
- Browser smoke: empty cart state, seeded localStorage cart state, order summary subtotal/count, dummy submit toast, no console errors.
- If harness requests canonical evidence and no suite applies, create `/tmp/hermes-verify-*.py`, check route order/static strings/live HTTP, then delete it and call result ad-hoc verification, not full suite green.
