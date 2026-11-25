FROM --platform=$BUILDPLATFORM node:26-alpine AS build
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /bin/uv
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY pipeline/pyproject.toml pipeline/uv.lock pipeline/.python-version pipeline/
RUN uv sync --project pipeline --locked --no-dev --no-install-project
COPY . .
ARG PUBLIC_PLAUSIBLE_SCRIPT
ARG PUBLIC_SENTRY_DSN
RUN uv run --project pipeline --no-dev leaves site && npm run build

FROM nginxinc/nginx-unprivileged:1.31-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/ > /dev/null || exit 1
