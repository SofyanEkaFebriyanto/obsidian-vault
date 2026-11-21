# Kenfa hero banner image fallback

Session pattern: homepage hero mockup required a product image, but seeded `banners.image` paths (`banners/hero-*.jpg`) pointed to missing files. Existing Blade guarded rendering with `file_exists(storage_path(...))`, so hero showed only gradient/text.

Frontend-only fix pattern:

1. Do not edit seeders, DB, controller, or storage assets when user says frontend-only.
2. In `resources/views/home.blade.php`, derive fallback products from already-passed homepage collections:
   - `collect([$newArrivals, $bestSellers])->flatten(1)->unique('id')->values()`
3. Per banner, prefer real banner asset if it exists:
   - `$banner->image && file_exists(storage_path('app/public/' . $banner->image)) ? asset('storage/' . $banner->image) : null`
4. If missing, pick matching product by comparing banner title and product name, else use slide index, else first product.
5. Use product `primaryImage` or first image path as fallback; final fallback can be `asset('images/placeholder-product.png')`.
6. Always render the hero `<img src="{{ $heroImageUrl }}">`; do not hide it behind `hidden lg:block` if mockup expects image-led hero.
7. Layout that matched intent: navy/gold gradient, 2-column desktop, image-first mobile, text-left desktop, large but not cropped product image (`max-w` and `scale` tuned after visual check).

Verification used:

- Build in Docker: `docker compose exec -T app npm run build`
- Ad-hoc `/tmp/hermes-verify-kenfa-hero.py` script checking fallback variables, always-rendered image, layout classes, live homepage HTML contains product/placeholder image source.
- Browser visual check confirmed product image appears in hero; if cropped, reduce max width / scale and rerun ad-hoc verification.

Pitfall:

- Missing banner assets are data/setup state, not reason to make backend changes. For frontend prototype, make graceful UI fallback from data already available in view.
