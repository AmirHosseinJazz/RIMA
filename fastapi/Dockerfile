# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

RUN apt-get update && apt-get install -y netcat-traditional \
    && pip install --no-cache-dir psycopg2-binary \
    && pip install -U prefect

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . ./app

# Command to run the FastAPI application
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]