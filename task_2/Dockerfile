# We are using Python as the base image.
FROM python:3.9-slim

# We are setting the working directory.
WORKDIR /app

# We are copying the Python application and its dependencies into the container.
COPY my_server.py /app/

# Install the necessary dependencies (you can use requirements.txt if needed).
RUN pip install --no-cache-dir --upgrade pip

# We are running the application on port 8080.
EXPOSE 8080

# The application startup command.
CMD ["python", "my_server.py"]