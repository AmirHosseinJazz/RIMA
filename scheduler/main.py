from prefect import flow, serve, get_client
from ingest import ingest_data
import time
import random


@flow(log_prints=True)
def data_start():
    time.sleep(random.randint(1, 10))
    ingest_data()


if __name__ == "__main__":
    scheduler = data_start.to_deployment(name="pipeline", cron="*/2 * * * *")
    serve(scheduler)
