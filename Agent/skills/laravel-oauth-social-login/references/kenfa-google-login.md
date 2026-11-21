# kenfa-2.0 — Google Login (verified green, 2026-09-07)

Concrete implementation that passed the full suite (208 passed). kenfa-2.0 is
Laravel 13 + Filament 5, guest-checkout-first, with a top-level catch-all
`/{slug}` route and a `ClaimGuestOrders` listener already wired to the `Login`
event. The pieces below slot into that setup.

## config/services.php (append inside the returned array)

```php
'services' => [
    // ...
    'google' => [
        'client_id' => env('GOOGLE_CLIENT_ID'),
        'client_secret' => env('GOOGLE_CLIENT_SECRET'),
        'redirect' => env('GOOGLE_REDIRECT_URI', 'http://localhost:8080/auth/google/callback'),
    ],
];
```

## .env / .env.example

```
# Google Login (Socialite) — isi dari Google Cloud Console (lihat .env.example)
# Kosongkan = tombol muncul tapi kliknya kembali dengan pesan (tanpa error).
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback
```

The `.env.example` comment should list the EXACT redirect URIs the owner
registers in Google Cloud Console (one per env):
```
#   https://test.kenfa.id/auth/google/callback
#   https://kenfa.id/auth/google/callback
```

## routes/web.php (inside the `guest` group, ABOVE the `/{slug}` catch-all)

```php
use App\Http\Controllers\Auth\GoogleController;
// ...
Route::middleware('guest')->group(function () {
    Route::get('/masuk', [LoginController::class, 'create'])->name('login');
    Route::post('/masuk', [LoginController::class, 'store']);

    // Google OAuth. Di atas catch-all /{slug} (Laravel tak fall-through).
    Route::get('/auth/google', [GoogleController::class, 'redirect'])->name('auth.google');
    Route::get('/auth/google/callback', [GoogleController::class, 'callback'])->name('auth.google.callback');
    // ...
});
```

## app/Http/Controllers/Auth/GoogleController.php

```php
<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Laravel\Socialite\Facades\Socialite;

class GoogleController extends Controller
{
    public function redirect(): RedirectResponse
    {
        // Feature OFF secara aman saat kredensial belum diisi: tombol tetap
        // dirender, tapi kliknya kembali ke /masuk dengan pesan.
        if (blank(config('services.google.client_id'))) {
            return redirect()->route('login')
                ->with('status', 'Login Google belum diaktifkan. Silakan masuk dengan email.');
        }
        return Socialite::driver('google')->redirect();
    }

    public function callback(Request $request): RedirectResponse
    {
        if (blank(config('services.google.client_id'))) {
            return redirect()->route('login')
                ->with('status', 'Login Google belum diaktifkan. Silakan masuk dengan email.');
        }

        try {
            $googleUser = Socialite::driver('google')->user();
        } catch (\Throwable $e) {
            // OAuth gagal (state tidak cocok, user tolak, dsb.) — jangan 500.
            Log::warning('Google login gagal', ['error' => $e->getMessage()]);
            return redirect()->route('login')
                ->with('status', 'Login Google gagal. Silakan coba lagi atau masuk dengan email.');
        }

        $email = $googleUser->getEmail();
        $isNew = false;

        // Atribut diset LANGSUNG (bukan fill/create): email_verified_at sengaja
        // di luar $fillable. password diisi string acak → cast 'hashed'
        // meng-hash saat save; kolom NOT NULL, login email ke akun ini tak mungkin lolos.
        $user = User::firstOrNew(['email' => $email]);
        if (! $user->exists) {
            $user->name = $googleUser->getName() ?? $googleUser->getNickname() ?? 'Pelanggan Kenfa';
            $user->password = Str::random(40);
            $user->email_verified_at = now();
            try {
                $user->save();
                $isNew = true;
            } catch (\Illuminate\Database\QueryException) {
                // Race dua tab: baris dibuat request kembar. Ambil ulang.
                $user = User::where('email', $email)->firstOrFail();
            }
        }

        Auth::login($user, remember: true);
        $request->session()->regenerate();
        // Auth::login melempar event Login → listener ClaimGuestOrders menautkan
        // order guest dengan email yang sama (user baru sudah verified).

        return redirect()->route('account.orders')
            ->with('status', $isNew
                ? 'Akun Google terhubung. Pesanan lama dengan email ini sudah ikut tertaut.'
                : 'Anda masuk dengan Google.');
    }
}
```

## tests/bootstrap.php — force the keys blank

```php
$forced = [
    'DB_CONNECTION' => 'sqlite',
    'DB_DATABASE' => ':memory:',
    // ... existing MIDTRANS_*, BITESHIP_API_KEY ...
    'GOOGLE_CLIENT_ID' => '',
    'GOOGLE_CLIENT_SECRET' => '',
];
```

## tests/Feature/GoogleLoginTest.php (the working stubs)

```php
<?php
namespace Tests\Feature;

use App\Models\Order;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Auth;
use Laravel\Socialite\Facades\Socialite;
use Tests\TestCase;

class GoogleLoginTest extends TestCase
{
    use RefreshDatabase;

    public function test_login_page_menampilkan_tombol_google(): void
    {
        $this->get('/masuk')->assertOk()->assertSee('Masuk dengan Google')->assertSee('/auth/google');
    }

    public function test_redirect_harmless_ketika_kredensial_belum_diisi(): void
    {
        $this->get('/auth/google')
            ->assertRedirect(route('login'))
            ->assertSessionHas('status');
    }

    public function test_callback_membuat_akun_verifikasi_dan_login(): void
    {
        $this->setGoogleProvider();
        $this->get('/auth/google/callback?code=apa-saja')->assertRedirect(route('account.orders'));

        $user = User::where('email', 'google-user@example.com')->first();
        $this->assertNotNull($user);
        $this->assertTrue($user->hasVerifiedEmail());
        $this->assertMatchesRegularExpression('/^\$2[aby]\$/', $user->password); // hash acak
        $this->assertSame('customer', $user->role);
        $this->assertAuthenticatedAs($user);
        $this->get('/akun/pesanan')->assertOk();
    }

    public function test_login_google_menautkan_pesanan_guest(): void
    {
        $order = Order::create([
            'user_id' => null,
            'order_number' => 'KNF'.now()->format('YmdHis').random_int(100, 999),
            'customer_name' => 'Guest Buyer',
            'customer_email' => 'google-user@example.com',
            'customer_phone' => '08123',
            'shipping_address' => 'Jl. Test 1',
            'shipping_city' => 'Bandung',
            'shipping_province' => 'Jawa Barat',
            'shipping_postal_code' => '40111',
            'subtotal' => 100000, 'shipping_cost' => 0, 'total' => 100000,
            'status' => 'pending', 'payment_method' => 'midtrans',
        ]);
        $this->setGoogleProvider();
        $this->get('/auth/google/callback?code=apa-saja')->assertRedirect(route('account.orders'));
        $this->assertSame(Auth::user()->id, $order->fresh()->user_id); // auto-claim
    }

    private function setGoogleProvider(): void
    {
        config()->set('services.google.client_id', 'test-client-id');
        config()->set('services.google.client_secret', 'test-client-secret');

        // MUST be User::fake() — `new Two\User([...])` leaves getEmail() null.
        $socialUser = \Laravel\Socialite\Two\User::fake([
            'id' => 'google-id-123',
            'nickname' => 'google-user',
            'name' => 'Google User',
            'email' => 'google-user@example.com',
        ]);

        Socialite::extend('google', fn () => new class($socialUser) {
            public function __construct(private object $user) {}
            public function user(): object { return $this->user; }
        });
    }
}
```

## The debugging path that got it green (for when the callback "404s")

Symptom: `assertRedirect(route('account.orders'))` fails, actual = 404, and
`route:list` shows the route is fine. Root cause was NOT routing:

1. First I suspected `Socialite::extend()` broke the route — wrong.
2. Ran the request with **`$this->withoutExceptionHandling();`** and printed
   `$e->getTrace()`. It revealed:
   `ModelNotFoundException ... at Builder.php:786 (firstOrFail)`, called from
   `GoogleController.php:78`.
3. That line was the race-recovery `firstOrFail` — which only runs after a
   `save()` `QueryException`. So `save()` was throwing: `users.password` is
   **NOT NULL** and I'd set it to `null`.
4. Fix: `$user->password = Str::random(40);` (hashed cast does the rest).
   Re-ran → green.

Lesson: when a controller `catch (\Throwable)` redirects, a 404 you see is
usually a *swallowed* exception rendering the custom 404 page. Always
`withoutExceptionHandling()` + `getTrace()` before debugging routes.

## Verify the real redirect (before asking the owner for keys)

With real keys in `.env`, spin the dev server and confirm it points at Google:
```
php artisan serve --host=127.0.0.1 --port=8080 &
curl -s -D - -o /dev/null http://127.0.0.1:8080/auth/google | grep -i '^location'
# → Location: https://accounts.google.com/o/oauth2/auth?client_id=<your-id>...
```
If the Location host is `accounts.google.com` and carries your `client_id`,
the OAuth handshake will succeed once the owner registers that client.
