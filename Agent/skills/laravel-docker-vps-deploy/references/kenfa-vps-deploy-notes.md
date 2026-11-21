# kenfa-2.0 deploy session notes (82.153.126.137, Aug 2026)

Concrete values from the successful run — use as reference points for similar Laravel deploys.

## Target
- VPS: ubuntu@82.153.126.137 (vps1-3), Ubuntu, 4 core / 3.8 GB RAM / 58 GB disk
- SSH key used: `~/.ssh/tokoserver` with `-o IdentitiesOnly=yes` (password login was swapped to key via sshpass+ssh-copy-id)

## App facts that shaped testing
- Compose: app (php artisan serve :8080) + mysql 8 (:3308 host) + phpmyadmin (:8888 host)
- Checkout POST requires: structured ids (`shipping_province_id`, `shipping_city_id`, `shipping_district_id` validated hierarchically in DB), `cart` JSON with `{"variantId": N, "quantity": N}` keys (camelCase from the Alpine cart store — NOT variant_id/qty)
- Cart JSON keys found by reading `app/Support/Cart.php::parse()` when the first payload bounced
- Test order KNF202608230001 created (subtotal Rp165.000, stok 10→9), then deleted + stock restored

## Commands proven to work on this stack
```bash
# composer when app container is crash-looping (no vendor yet)
docker run --rm -v ~/apps/kenfa/src:/var/www/html -w /var/www/html kenfa-app \
  composer install --no-interaction --no-dev --optimize-autoloader

# chown storage back after root contamination
docker exec -u root kenfa-app sh -c "rm -rf /var/www/html/storage/framework/testing/disks && chown -R 1000:1000 /var/www/html/storage/framework/testing"

# csrf-gated checkout probe pattern lives in the main SKILL.md; script was scp'd in,
# docker cp'd to the container, executed with `docker exec ... php kf_checkout.php`, then removed.
```

## Left open on this deployment
- phpMyAdmin exposed :8888 with default rootsecret password
- Midtrans/Biteship env blank → orders fall back to manual-transfer path (by design)
- No domain/HTTPS yet (raw IP); Cloudflare tunnel is user's preferred permanent route
