# Dashboard

Next.js control surface for triggering and monitoring generation workflows.

## Development

```bash
npm run dev
```

Runs on [http://localhost:6767](http://localhost:6767).

## Quality Checks

```bash
npm run lint
npm run test
```

## Build

```bash
npm run build
npm run start
```

## Notes

- API trigger route: `src/app/api/generate/route.ts`
- UI entrypoint: `src/app/page.tsx`
- Uses project-level Python CLI under `../dj_msqrvve_brand_system`

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
