#!/usr/bin/env bash
set -e

ROOT_USER="${1:-root}"
ROOT_PASS="${2:-rootpass}"
DB_NAME="${3:-aix_decision_db}"
APP_USER="${4:-aix_user}"
APP_PASS="${5:-aix_pass}"
HOST="${6:-127.0.0.1}"
PORT="${7:-3306}"

echo "Creating DB=${DB_NAME}, USER=${APP_USER} on ${HOST}:${PORT}"

mysql -h"${HOST}" -P"${PORT}" -u"${ROOT_USER}" -p"${ROOT_PASS}" -e "
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${APP_USER}'@'%' IDENTIFIED BY '${APP_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${APP_USER}'@'%';
FLUSH PRIVILEGES;
"

echo "MySQL setup complete."
echo "DATABASE_URL=mysql+pymysql://${APP_USER}:${APP_PASS}@${HOST}:${PORT}/${DB_NAME}"
