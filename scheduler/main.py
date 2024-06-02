from prefect import flow, serve, get_client
from ingest import ingest_data


@flow(log_prints=True)
def data_start():
    ingest_data()


if __name__ == "__main__":
    scheduler = data_start.to_deployment(name="pipeline", cron="*/1 * * * *")
    serve(scheduler)
