#!bin/bash

set -e # exit on error

echo "Starting deploy!"

if [ ! -f .env]; then
  echo "error .env file not found!"
  exit 1
fi


echo "Building new images..."

docker compose -f docker-compose.prod.yml --env-file .env build --no-cache

docker compose -f docker-compose.prod.yml --env-file .env up -d --force-recreate --remove-orphans

sleep 15

docker compose -f docker-compose.prod.yml --env-file .env exec -T app python src/manage.py collectstatic --no-input

docker image prune -f

echo "completed!"

