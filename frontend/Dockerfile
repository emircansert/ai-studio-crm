# Borusan AI Ecosystem CRM - frontend (Next.js)
#
# Build from the frontend directory:
#   docker build -t borusan-crm-frontend ./frontend \
#     --build-arg NEXT_PUBLIC_ENTRA_CLIENT_ID=<client-id> \
#     --build-arg NEXT_PUBLIC_ENTRA_TENANT_ID=<tenant-id> \
#     --build-arg NEXT_PUBLIC_ENTRA_REDIRECT_URI=https://library.borusan.com
#
# NEXT_PUBLIC_ENTRA_REDIRECT_URI is the BASE origin only; the app appends the
# dedicated callback path /auth/callback. The redirect URI registered in Azure
# (SPA platform) must be the full <base>/auth/callback value.
# Run:
#   docker run -e BACKEND_API_ORIGIN=http://backend:8001 -p 3000:3000 borusan-crm-frontend
#
# There is deliberately no API-scope build arg: the app registration grants only
# delegated Microsoft Graph permissions and exposes no custom API, so sign-in
# uses openid/profile/email/User.Read and the CRM API is authenticated with the
# OIDC ID token.
#
# NOTE: NEXT_PUBLIC_* values are compiled into the client bundle at BUILD time
# (standard Next.js behaviour). None of them are secrets: the Entra client id,
# tenant id, and redirect URI are public OIDC metadata. The client SECRET is
# never used by this app (MSAL PKCE public-client flow) and must not be passed
# here. Runtime-only variables: BACKEND_API_ORIGIN (server-side proxy target).

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
ARG NEXT_PUBLIC_ENTRA_CLIENT_ID=
ARG NEXT_PUBLIC_ENTRA_TENANT_ID=
ARG NEXT_PUBLIC_ENTRA_REDIRECT_URI=
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_ENTRA_CLIENT_ID=$NEXT_PUBLIC_ENTRA_CLIENT_ID \
    NEXT_PUBLIC_ENTRA_TENANT_ID=$NEXT_PUBLIC_ENTRA_TENANT_ID \
    NEXT_PUBLIC_ENTRA_REDIRECT_URI=$NEXT_PUBLIC_ENTRA_REDIRECT_URI \
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
