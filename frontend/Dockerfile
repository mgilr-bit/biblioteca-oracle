# --- Etapa 1: build de la app Vue ---
# Node 24 (LTS): Vite 8 exige Node >= 20.19 y Node 20 ya no tiene soporte.
# Trae npm 11.x, que respeta `min-release-age` del .npmrc durante `npm ci`.
FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# VITE_API_URL se puede sobreescribir en build con --build-arg
ARG VITE_API_URL=http://localhost:5000/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# --- Etapa 2: servir estáticos con nginx ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
