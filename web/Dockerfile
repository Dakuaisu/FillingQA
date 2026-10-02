# FilingQA frontend (PRD 10). API_BASE points at the API at run time.
FROM node:24-slim AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:24-slim
WORKDIR /web
ENV NODE_ENV=production
COPY --from=build /web/package.json /web/package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /web/.next ./.next
COPY --from=build /web/public ./public
COPY --from=build /web/next.config.ts ./next.config.ts
EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"]
