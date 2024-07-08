# Use the official Python image as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install Flask and other dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the Flask app code to the container
COPY . .

# Expose the port the Flask app runs on
EXPOSE 5000

# Command to run the Flask app in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
