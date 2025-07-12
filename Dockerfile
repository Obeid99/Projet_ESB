# --- Frontend Stage ---
FROM node:20-alpine AS frontend

WORKDIR /frontend
COPY package.json yarn.lock* package-lock.json* ./
RUN yarn install --frozen-lockfile || npm install
COPY . .
RUN yarn build || npm run build

# --- Backend Stage ---
FROM python:3.12-slim AS backend

RUN apt-get update && \
    apt-get install -y supervisor && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend-production/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend-production/ ./

# --- Final Stage ---
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y supervisor nodejs npm && \
    npm install -g yarn && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend from backend stage
COPY --from=backend /app /app

# Copy frontend build from frontend stage
COPY --from=frontend /frontend/.next /app/.next
COPY --from=frontend /frontend/public /app/public
COPY --from=frontend /frontend/package.json /app/package.json

# Supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV FLASK_APP=src/web/web_interface.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

EXPOSE 5000
EXPOSE 3000

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
