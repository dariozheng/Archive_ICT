# webnovel

A blank Next.js 15 starter, pre-wired for the homelab. The scaffold gives you
a deployed "hello" page that proves the whole infrastructure path works
(Caddy → reverse-proxy → Node → React). From there, you fill in pages, API
routes, DB, auth, caching, and UI as you go.

This README is the **build-around guide**. The homelab guide §13 covers
operations (deploy, restart, monitor). Everything else lives here.

---

## Table of contents

1. [What's in the scaffold](#1-whats-in-the-scaffold)
2. [Dev loop](#2-dev-loop)
3. [Routing — adding pages](#3-routing--adding-pages)
4. [API routes — adding endpoints](#4-api-routes--adding-endpoints)
5. [Server Components vs Client Components](#5-server-components-vs-client-components)
6. [Server Actions — mutations from the client](#6-server-actions--mutations-from-the-client)
7. [Reading `params` and `searchParams`](#7-reading-params-and-searchparams)
8. [Caching — `revalidate`, `unstable_cache`, `revalidateTag`](#8-caching)
9. [Fonts — `next/font`](#9-fonts--nextfont)
10. [Styling — Tailwind v4](#10-styling--tailwind-v4)
11. [Wiring a database (Postgres)](#11-wiring-a-database-postgres)
12. [Wiring auth (Better Auth)](#12-wiring-auth-better-auth)
13. [Environment variables](#13-environment-variables)
14. [Static files](#14-static-files)
15. [Production build + deploy](#15-production-build--deploy)
16. [Project layout — suggested as you grow](#16-project-layout--suggested-as-you-grow)

---

## 1. What's in the scaffold

```
webnovel/
├── package.json              # next 15, react 19, typescript, tailwind v4 — no other deps
├── tsconfig.json             # strict mode, @/* path alias for src/
├── next.config.ts            # output: 'standalone', images.unoptimized: true
├── postcss.config.mjs        # @tailwindcss/postcss
├── Dockerfile                # multi-stage Alpine, ~250 MB final image
├── docker-compose.yml        # static IP 172.31.0.50 on proxy-net
├── .env.example              # placeholder
├── src/
│   └── app/
│       ├── layout.tsx        # root layout — html/body wrapper
│       ├── page.tsx          # the welcome page you see at /
│       ├── globals.css       # Tailwind v4 import + @theme tokens
│       └── api/
│           └── health/
│               └── route.ts  # GET /api/health — healthcheck for Docker + Kuma
└── public/                   # static files served at /
```

That's it. No DB, no auth, no components, no utilities, no fonts. Add what
you need when you need it.

---

## 2. Dev loop

Run locally (no Docker) for the fastest feedback:

```bash
npm install
npm run dev
# http://localhost:3000 — edit src/app/page.tsx, save, page reloads
```

Type-check before committing:

```bash
npm run typecheck            # tsc --noEmit, finds errors `next dev` may skip
npm run build                # full production build — same thing the Docker image does
```

The Docker `docker compose up --build` flow rebuilds the whole image on
every change (slow). Use it for verifying deploys, not for iteration.

---

## 3. Routing — adding pages

Next.js App Router uses **file-based routing**. The path to a `page.tsx`
file under `src/app/` becomes the URL.

| File | URL |
|---|---|
| `src/app/page.tsx` | `/` |
| `src/app/about/page.tsx` | `/about` |
| `src/app/novels/page.tsx` | `/novels` |
| `src/app/novels/[slug]/page.tsx` | `/novels/anything` (dynamic) |
| `src/app/novels/[slug]/[chapter]/page.tsx` | `/novels/foo/3` (nested dynamic) |
| `src/app/(marketing)/about/page.tsx` | `/about` (the `(marketing)` is a "route group" — folders in parens don't appear in the URL, useful for grouping pages that share a layout) |

Each page is a Server Component by default — runs on the server, returns
HTML, ships zero JS for that component to the client.

Minimal page example:

```tsx
// src/app/about/page.tsx
export default function AboutPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-20">
      <h1 className="text-4xl font-semibold">About</h1>
      <p className="mt-4 text-[var(--color-muted)]">Hello.</p>
    </main>
  );
}
```

Drop the file, visit `/about` — no config, no router registration needed.

### Nested layouts

Drop a `layout.tsx` next to a `page.tsx` and it wraps every page in that
folder and its children. Useful for shared chrome (header, footer, side nav):

```tsx
// src/app/(app)/layout.tsx — wraps everything under (app)
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b border-[var(--color-rule)] p-4">My App</header>
      <div>{children}</div>
    </>
  );
}
```

### Loading + error states

- `loading.tsx` — Suspense fallback shown while a page's data loads
- `error.tsx` — error boundary catching exceptions in a page

```tsx
// src/app/novels/loading.tsx
export default function Loading() {
  return <div className="p-20 text-center text-[var(--color-muted)]">Loading…</div>;
}
```

### `not-found.tsx`

```tsx
// src/app/novels/[slug]/not-found.tsx
export default function NotFound() {
  return <p className="p-20 text-center">Novel not found.</p>;
}
```

Trigger it from a page:

```tsx
import { notFound } from 'next/navigation';
if (!data) notFound();
```

---

## 4. API routes — adding endpoints

Use **Route Handlers** under `src/app/api/`. Export one async function per
HTTP verb.

```ts
// src/app/api/novels/route.ts — GET /api/novels and POST /api/novels
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ novels: [] });
}

export async function POST(req: Request) {
  const body = await req.json();
  // validate, write to DB, etc.
  return NextResponse.json({ created: true }, { status: 201 });
}
```

Dynamic segments work like pages:

```ts
// src/app/api/novels/[slug]/route.ts
export async function GET(
  _req: Request,
  ctx: { params: Promise<{ slug: string }> },
) {
  const { slug } = await ctx.params;     // Next 15 makes params a Promise — must await
  return NextResponse.json({ slug });
}
```

To opt out of caching (force fresh on every request):

```ts
export const dynamic = 'force-dynamic';
```

---

## 5. Server Components vs Client Components

**Server Components** (the default) run on the server. They can:
- `await` data directly (no `useEffect`, no `useState` for fetching)
- Read cookies, headers, env vars
- Connect to databases
- Import secrets safely (they never reach the client)

They **cannot**:
- Use `useState`, `useEffect`, or any React hook
- Attach `onClick`/`onChange` etc. handlers
- Use browser-only APIs (`window`, `document`, `localStorage`)

**Client Components** opt in with `'use client'` at the top of the file. They:
- Run in the browser (after a JS bundle is sent down)
- Can use hooks, event handlers, browser APIs
- Cannot `await` directly in the component body

```tsx
// src/components/Counter.tsx
'use client';

import { useState } from 'react';

export default function Counter() {
  const [n, setN] = useState(0);
  return <button onClick={() => setN((x) => x + 1)}>Count: {n}</button>;
}
```

A Server Component can render a Client Component — Next handles the
hand-off. The other way (Client → Server) is not possible directly, but
you can pass Server Components as `children` props.

**Rule of thumb:** keep components as Server by default. Only opt into
Client for the interactive leaves of your component tree.

---

## 6. Server Actions — mutations from the client

Server Actions let a Client Component call a typed server function
without writing an API route.

```tsx
// src/actions/novels.ts
'use server';

import { revalidatePath } from 'next/cache';

export async function createNovel(formData: FormData) {
  const title = formData.get('title') as string;
  // ... write to DB ...
  revalidatePath('/novels');             // bust the cached novel list
}
```

```tsx
// src/app/novels/new/page.tsx — a form that invokes the action
import { createNovel } from '@/actions/novels';

export default function NewNovelPage() {
  return (
    <form action={createNovel} className="space-y-4 p-6">
      <input name="title" required className="border px-3 py-2" />
      <button className="bg-[var(--color-accent)] px-4 py-2 text-white">
        Create
      </button>
    </form>
  );
}
```

The form `action` accepts a server function directly — no `onSubmit`, no
`fetch`, no API route, no client JS for the form itself. Progressive
enhancement out of the box.

For optimistic UI from a client component, use `useTransition` + `useOptimistic`:

```tsx
'use client';
import { useTransition, useOptimistic } from 'react';
import { toggleBookmark } from '@/actions/bookmarks';

export default function BookmarkButton({ novelId, isBookmarked }: { ... }) {
  const [optimistic, setOptimistic] = useOptimistic(isBookmarked);
  const [pending, start] = useTransition();

  return (
    <button
      onClick={() => start(async () => {
        setOptimistic(!optimistic);
        await toggleBookmark(novelId);
      })}
      disabled={pending}
    >
      {optimistic ? '★ Saved' : '☆ Save'}
    </button>
  );
}
```

---

## 7. Reading `params` and `searchParams`

**Next.js 15 made these async.** They are Promises that must be awaited:

```tsx
// src/app/novels/[slug]/page.tsx
type Props = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string; sort?: string }>;
};

export default async function NovelPage({ params, searchParams }: Props) {
  const { slug } = await params;
  const { page = '1', sort = 'recent' } = await searchParams;
  // ...
}
```

Same for `generateMetadata`:

```tsx
export async function generateMetadata({ params }: Props) {
  const { slug } = await params;
  return { title: `Novel: ${slug}` };
}
```

If you forget `await`, TypeScript will complain — the strict tsconfig
catches this.

---

## 8. Caching

Next.js has three layers of cache. Knowing which to reach for matters.

### Layer 1 — Route segment cache (`export const revalidate`)

In a `page.tsx` or `route.ts`:

```ts
export const revalidate = 3600;          // re-render every hour
export const revalidate = 0;             // never cache (same as `force-dynamic`)
export const dynamic = 'force-dynamic';  // explicit opt-out
```

### Layer 2 — Granular cache (`unstable_cache`)

Wrap a function so it's memoised, tagged, and revalidatable independently:

```ts
import { unstable_cache } from 'next/cache';

export const getPopularNovels = unstable_cache(
  async () => {
    return db.query.novels.findMany({ ... });
  },
  ['popular-novels'],                    // unique key for the cache entry
  { tags: ['novels', 'popular'], revalidate: 300 },
);
```

### Layer 3 — Tag-based invalidation

From a Server Action or Route Handler, bust everything tagged with a name:

```ts
import { revalidateTag, revalidatePath } from 'next/cache';

revalidateTag('novels');                 // invalidates all cache entries with tag 'novels'
revalidatePath('/novels');               // invalidates a specific route's cache
```

**Pattern:** tag your cached queries by entity (`'novel:abc-123'`), and call
`revalidateTag` in the action that mutates that entity. Fine-grained
invalidation without flushing everything.

---

## 9. Fonts — `next/font`

Self-hosted Google Fonts with zero layout shift and automatic preloading:

```ts
// src/lib/fonts.ts
import { Inter, Source_Serif_4 } from 'next/font/google';

export const sans = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

export const serif = Source_Serif_4({
  subsets: ['latin'],
  variable: '--font-serif',
  axes: ['opsz'],                        // variable-font axes are optional
  display: 'swap',
});
```

Apply the CSS variable in the root layout:

```tsx
// src/app/layout.tsx
import { sans, serif } from '@/lib/fonts';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

Then in `globals.css`, reference the variables:

```css
@theme {
  --font-sans: var(--font-sans);
  --font-serif: var(--font-serif);
}
body { font-family: var(--font-sans); }
.font-serif { font-family: var(--font-serif); }
```

---

## 10. Styling — Tailwind v4

v4 uses **CSS-first config** — `@theme` blocks in `globals.css` define the
design tokens, no `tailwind.config.js` needed.

```css
@theme {
  --color-brand: #7c3aed;                /* now `bg-brand`, `text-brand`, `border-brand` work */
  --spacing-72: 18rem;                   /* now `mt-72`, `p-72` work */
  --font-display: 'Fraunces', serif;     /* now `font-display` works */
}
```

Dark mode: wrap a separate `@theme` in `@media (prefers-color-scheme: dark)`
(as the starter does) or use a `[data-theme="dark"]` selector if you want
manual toggling.

Tailwind v4 utilities are auto-generated from the theme tokens. The output
CSS is much smaller than v3 because unused utilities never get generated.

---

## 11. Wiring a database (Postgres)

The homelab has a `postgres:18.4-alpine` container. To use it:

1. Make sure `postgres` is attached to `proxy-net` (one-time, via Portainer
   or `docker network connect proxy-net postgres`)
2. In Postgres, create a database + user for this app:
   ```sql
   CREATE USER webnovel WITH PASSWORD '<strong-random>';
   CREATE DATABASE webnovel OWNER webnovel;
   ```
3. Install the driver:
   ```bash
   npm i postgres                       # postgres-js, smaller + faster than node-pg
   ```
4. Create a singleton client:
   ```ts
   // src/lib/db.ts
   import postgres from 'postgres';
   const globalForDb = globalThis as unknown as { __pg?: ReturnType<typeof postgres> };
   export const sql =
     globalForDb.__pg ??
     postgres(process.env.DATABASE_URL!, { max: 10, prepare: false });
   if (process.env.NODE_ENV !== 'production') globalForDb.__pg = sql;
   ```
5. Query:
   ```ts
   import { sql } from '@/lib/db';
   const novels = await sql`SELECT * FROM novels ORDER BY created_at DESC LIMIT 10`;
   ```
6. Set `DATABASE_URL` in `.env` and in the Portainer stack env vars:
   ```
   DATABASE_URL=postgres://webnovel:<pw>@postgres:5432/webnovel
   ```

**For typed queries + migrations**, layer Drizzle on top:

```bash
npm i drizzle-orm
npm i -D drizzle-kit
```

Define a schema in `src/lib/db/schema.ts`, generate SQL with
`drizzle-kit generate`, apply with `drizzle-kit migrate`. Pattern is
covered in detail in the Drizzle docs.

---

## 12. Wiring auth (Better Auth)

When you want sign-in:

```bash
npm i better-auth
```

```ts
// src/lib/auth.ts
import { betterAuth } from 'better-auth';

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL!,
  secret: process.env.BETTER_AUTH_SECRET!,
  // database: drizzleAdapter(db, { provider: 'pg', schema: { ... } }),
  emailAndPassword: { enabled: true, minPasswordLength: 12 },
});
```

```ts
// src/app/api/auth/[...all]/route.ts
import { auth } from '@/lib/auth';
import { toNextJsHandler } from 'better-auth/next-js';
export const { POST, GET } = toNextJsHandler(auth);
```

Generate the auth secret:

```bash
openssl rand -base64 32
```

Better Auth's docs cover the schema your DB needs (`user`, `session`,
`account`, `verification` tables). The Drizzle adapter wires them up.

---

## 13. Environment variables

- `.env` for production secrets — never commit
- `.env.local` for personal dev overrides
- Variables prefixed `NEXT_PUBLIC_` are inlined into the client bundle;
  everything else stays server-only

Read them with `process.env.WHATEVER`. For type safety, declare them once:

```ts
// src/env.ts
const required = ['DATABASE_URL', 'BETTER_AUTH_SECRET'] as const;
for (const k of required) if (!process.env[k]) throw new Error(`${k} not set`);

export const env = {
  DATABASE_URL: process.env.DATABASE_URL!,
  BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET!,
};
```

Importing `env` instead of `process.env` directly guarantees you fail at
boot, not on the first request that needs a missing var.

---

## 14. Static files

Anything under `public/` is served at the root URL:

- `public/favicon.ico` → `/favicon.ico`
- `public/images/cover.jpg` → `/images/cover.jpg`

In components, just reference the path:

```tsx
<img src="/images/cover.jpg" alt="" />
```

For optimised images (responsive `srcset`, modern formats), use `next/image`
— but since we disabled the optimiser in `next.config.ts` for the Pi, you
get plain `<img>` behaviour. Re-enable it in `next.config.ts` if you move
to a cloud host with image-optimisation infrastructure (Vercel includes it).

---

## 15. Production build + deploy

**Local typecheck + build:**

```bash
npm run typecheck
npm run build                            # outputs .next/standalone + .next/static
```

**Deploy to the Pi homelab:** see homelab guide §13. Short version:

```bash
# One-time: place project under /opt/webnovel
sudo mkdir -p /opt/webnovel && sudo chown -R $USER:$USER /opt/webnovel
cd /opt/webnovel && unzip ~/webnovel.zip -d /tmp && mv /tmp/webnovel/* . && mv /tmp/webnovel/.* . 2>/dev/null

# Build the image (CLI is faster than Portainer's Repository-build mode):
docker compose build                     # ~4 min on Pi 5, first time

# Deploy via Portainer:
#   Stacks → Add stack → Web editor → paste docker-compose.yml → Deploy
# Or via CLI:
docker compose up -d
docker logs -f webnovel
```

Then wire Caddy + Pi-hole (homelab §13.4 — one line each).

---

## 16. Project layout — suggested as you grow

You don't have to follow this; Next.js doesn't enforce structure beyond
`src/app/`. But here's a layout that scales:

```
webnovel/
├── src/
│   ├── app/                # routing + pages + layouts + route handlers
│   ├── components/         # presentational React components (NovelCard, etc.)
│   ├── actions/            # 'use server' functions (mutations)
│   ├── lib/                # non-React helpers
│   │   ├── db/             # database client + schema + queries
│   │   ├── auth.ts         # auth setup
│   │   ├── utils.ts        # generic helpers
│   │   └── fonts.ts        # next/font instances
│   ├── env.ts              # env var schema + validation
│   └── middleware.ts       # Edge middleware (route guards, headers)
├── public/                 # static files served at /
└── drizzle/                # if using Drizzle: migrations + schema
```

Server Components live alongside pages in `app/`; reusable Client Components
live in `components/`. `lib/` is anything you'd test in isolation. `actions/`
keeps mutations together so they're easy to find.

Rename, restructure, or ignore any of this — the project is yours.

---

## Useful links

- Next.js 15 docs: https://nextjs.org/docs
- App Router conventions: https://nextjs.org/docs/app/api-reference/file-conventions
- Server Components vs Client: https://nextjs.org/docs/app/getting-started/server-and-client-components
- Server Actions: https://nextjs.org/docs/app/getting-started/updating-data
- Caching deep dive: https://nextjs.org/docs/app/deep-dive/caching
- Tailwind v4: https://tailwindcss.com/docs
- Better Auth: https://www.better-auth.com
- Drizzle ORM: https://orm.drizzle.team
