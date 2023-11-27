# Use an official Python runtime as a parent image
FROM python:3.11.4

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn gevent-websocket eventlet

# Expose the port that the app runs on
EXPOSE 80

# Run Gunicorn when the container launches
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:80", "--worker-class", "eventlet", "app:app"]
