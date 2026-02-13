# --- ÉTAPE 1 : BUILD ---
FROM node:lts-alpine AS build-stage

WORKDIR /app

# On ne garde python/make/g++ que si tes paquets npm en ont vraiment besoin
RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm install

# Injection de l'URL API (Crucial pour que le front trouve le back via /k-guard/api)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
ENV NODE_ENV=production

COPY . .
RUN npm run build

# --- ÉTAPE 2 : PRODUCTION ---
FROM nginx:stable-alpine AS production-stage

# Nettoyage pour éviter les conflits avec les fichiers par défaut d'Nginx
RUN rm -rf /usr/share/nginx/html/*

# On copie le build final vers la racine (servie via 'alias' dans nginx.conf)
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Injection de ta config Nginx avec la directive 'alias'
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]