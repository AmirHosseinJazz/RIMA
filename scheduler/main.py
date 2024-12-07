from prefect import flow, serve, get_client
from ingest import ingest_data,clean_data
import time
import random


@flow(log_prints=True)
def data_start():
    time.sleep(random.randint(1, 10))
    ingest_data()

@flow(log_prints=True)
def clean_db():
    print("Data cleaned")
    clean_data()


if __name__ == "__main__":
    scheduler = data_start.to_deployment(name="pipeline", cron="*/2 * * * *")
    cleaner = clean_db.to_deployment(name="cleaner", cron="0 0 */3 * *")
    serve(scheduler, cleaner)
