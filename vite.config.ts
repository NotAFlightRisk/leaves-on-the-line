import { sentryVitePlugin } from '@sentry/vite-plugin';
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

const plausible = process.env.PUBLIC_PLAUSIBLE_SCRIPT ?? '';
const pulse = plausible ? [new URL(plausible).origin as `${string}.${string}`] : [];
const sentry = process.env.PUBLIC_SENTRY_DSN ?? '';
const oops = sentry ? [new URL(sentry).origin as `${string}.${string}`] : [];
const uploadMaps = Boolean(process.env.SENTRY_AUTH_TOKEN && process.env.SENTRY_URL);
const tiles = 'https://tiles.openfreemap.org';

export default defineConfig({
  define: {
    'import.meta.env.PUBLIC_PLAUSIBLE_SCRIPT': JSON.stringify(plausible),
    'import.meta.env.PUBLIC_SENTRY_DSN': JSON.stringify(sentry)
  },
  build: {
    sourcemap: uploadMaps && 'hidden',
    assetsInlineLimit: (file) => (/\.woff2?$/.test(file) ? false : undefined)
  },
  plugins: [
    sveltekit({
      compilerOptions: {
        runes: ({ filename }) =>
          filename.split(/[/\\]/).includes('node_modules') ? undefined : true
      },
      adapter: adapter({ fallback: '404.html' }),
      paths: { relative: false },
      prerender: { entries: ['*', '/sitemap.xml'] },
      csp: {
        mode: 'hash',
        directives: {
          'default-src': ['self'],
          'script-src': ['self', ...pulse],
          'connect-src': ['self', tiles, ...pulse, ...oops],
          'img-src': ['self', 'data:', 'blob:'],
          'worker-src': ['self', 'blob:'],
          'style-src': ['self', 'unsafe-inline'],
          'font-src': ['self'],
          'base-uri': ['none'],
          'form-action': ['self']
        }
      }
    }),
    uploadMaps &&
      sentryVitePlugin({
        telemetry: false,
        release: { create: false, finalize: false, setCommits: false, deploy: false },
        bundleSizeOptimizations: { excludeDebugStatements: true, excludeTracing: true },
        sourcemaps: {
          assets: '.svelte-kit/output/client/**',
          filesToDeleteAfterUpload: '.svelte-kit/output/**/*.map'
        }
      })
  ],
  test: {
    include: ['tests/**/*.test.ts']
  }
});
