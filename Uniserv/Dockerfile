# Étape 1 : construction du site (React) en fichiers statiques.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Même origine que l'API : le site et l'API sont servis par le même nginx.
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Étape 2 : nginx sert le site et relaie /api vers Django.
# Image nginx sans privilèges (utilisateur non-root, port 8080) : acceptée par les
# politiques de sécurité strictes des clusters Kubernetes.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
