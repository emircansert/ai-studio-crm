# Borusan AI Ecosystem CRM - frontend (Next.js)
#
# Build from the frontend directory:
#   docker build -t borusan-crm-frontend ./frontend \
#     --build-arg NEXT_PUBLIC_AUTH_MODE=entra \
#     --build-arg NEXT_PUBLIC_ENTRA_CLIENT_ID=<client-id> \
#     --build-arg NEXT_PUBLIC_ENTRA_TENANT_ID=<tenant-id> \
#     --build-arg NEXT_PUBLIC_ENTRA_REDIRECT_URI=https://ecosystem.borusan.com \
#     --build-arg NEXT_PUBLIC_ENTRA_API_SCOPE=api://<client-id>/user_impersonation
# Run:
#   docker run -e BACKEND_API_ORIGIN=http://backend:8001 -p 3000:3000 borusan-crm-frontend
#
# NOTE: NEXT_PUBLIC_* values are compiled into the client bundle at BUILD time
# (standard Next.js behaviour). None of them are secrets: the Entra client id,
# tenant id, redirect URI, and scope are public OIDC metadata. The client
# SECRET is never used by this app (MSAL PKCE public-client flow) and must not
# be passed here. Runtime-only variables: BACKEND_API_ORIGIN (server-side
# proxy target).

# ---- deps ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- build ----
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_BASE_URL=/api/backend
ARG NEXT_PUBLIC_AUTH_MODE=entra
ARG NEXT_PUBLIC_ENTRA_CLIENT_ID=
ARG NEXT_PUBLIC_ENTRA_TENANT_ID=
ARG NEXT_PUBLIC_ENTRA_REDIRECT_URI=
ARG NEXT_PUBLIC_ENTRA_API_SCOPE=
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_AUTH_MODE=$NEXT_PUBLIC_AUTH_MODE \
    NEXT_PUBLIC_ENTRA_CLIENT_ID=$NEXT_PUBLIC_ENTRA_CLIENT_ID \
    NEXT_PUBLIC_ENTRA_TENANT_ID=$NEXT_PUBLIC_ENTRA_TENANT_ID \
    NEXT_PUBLIC_ENTRA_REDIRECT_URI=$NEXT_PUBLIC_ENTRA_REDIRECT_URI \
    NEXT_PUBLIC_ENTRA_API_SCOPE=$NEXT_PUBLIC_ENTRA_API_SCOPE \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---- runtime ----
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S crm && adduser -S crm -G crm

COPY --from=build --chown=crm:crm /app/.next/standalone ./
COPY --from=build --chown=crm:crm /app/.next/static ./.next/static

USER crm
EXPOSE 3000
CMD ["node", "server.js"]
