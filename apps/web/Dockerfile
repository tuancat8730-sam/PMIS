FROM node:22-alpine AS base

ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH \
    NEXT_TELEMETRY_DISABLED=1
RUN npm install -g pnpm@9

WORKDIR /srv/web

FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM base AS build
COPY --from=deps /srv/web/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* được nhúng vào bundle lúc build, nên phải truyền qua build arg.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN pnpm build

FROM base AS runtime
ENV NODE_ENV=production
COPY --from=build /srv/web/package.json ./
COPY --from=build /srv/web/public ./public
COPY --from=build /srv/web/.next ./.next
COPY --from=build /srv/web/node_modules ./node_modules

EXPOSE 3000
CMD ["pnpm", "start", "-p", "3000", "-H", "0.0.0.0"]
