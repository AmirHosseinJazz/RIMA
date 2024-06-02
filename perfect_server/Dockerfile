FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-traditional 

RUN pip install --no-cache-dir psycopg2-binary

RUN pip install -U prefect

# Install requirements
COPY ./requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 4200

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
