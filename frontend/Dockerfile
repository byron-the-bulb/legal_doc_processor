# Stage 1: Build static assets with Vite
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# Point frontend to same-origin reverse proxy (/api)
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

# Stage 2: Serve with Nginx and reverse proxy /api to backend
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
