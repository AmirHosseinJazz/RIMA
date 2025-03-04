#!/bin/bash
echo "Preparing environment..."
./prepare_env.sh

echo " ====> Starting Docker Compose <===="
docker-compose up --build "$@"
# docker compose up "$@"
