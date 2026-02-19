#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying org-management..."

APP_DIR="/home/emarat/org-management"
cd "$APP_DIR"

echo "📥 Pulling latest code..."
git pull origin master

echo "🐳 Building images..."
docker compose build

echo "🧹 Stopping old containers..."
docker compose down

echo "▶️ Starting new containers..."
docker compose up -d

echo "🧪 Checking status..."
docker compose ps

echo "✅ Deployment complete"
