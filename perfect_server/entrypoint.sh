#!/bin/bash
set -e

wait_for_postgres() {
    echo "Waiting for postgres..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
}

wait_for_prefect() {
    echo "Waiting for Prefect..."
    while ! nc -z 0.0.0.0 4200; do
      sleep 0.1
    done
    echo "Prefect started"
}


# Call the function with environment variables
wait_for_postgres

echo "Running entrypoint for workflow"

prefect server start 