# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir instagrapi asyncio Pillow python-dotenv

# Command to run your script
CMD ["python", "post_comments.py"]
