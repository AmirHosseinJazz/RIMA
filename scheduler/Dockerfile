# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

RUN apt-get update && apt-get install -y netcat-traditional \
    && pip install --no-cache-dir psycopg2-binary 
# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install lxml[html_clean]

# Copy the rest of the code into the container
COPY . ./app

RUN chmod +x ./app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]

# Command to run the FastAPI application
CMD ["python","main.py"]