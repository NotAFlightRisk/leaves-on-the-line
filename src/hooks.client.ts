import type { ClientInit, HandleClientError } from '@sveltejs/kit/hooks';
import { loadPlausible } from '#lib/plausible.ts';

const dsn = import.meta.env.PUBLIC_SENTRY_DSN;
let sentry: Promise<(error: unknown) => void> | undefined;

// the SDK only downloads once something's broken, and a failed download drops the report
function report(error: unknown) {
  sentry ??= import('#lib/sentry.ts').then(({ start }) => start(dsn)).catch(() => () => {});
  sentry.then((capture) => capture(error));
}

if (dsn) {
  addEventListener('error', (event) => event.error && report(event.error));
  addEventListener('unhandledrejection', (event) => report(event.reason));
}

export const handleError: HandleClientError = ({ kind, error }) => {
  if (dsn && kind === 'unknown') report(error);
};

// before any page mounts, so a 404 on arrival still counts
export const init: ClientInit = () => loadPlausible();
