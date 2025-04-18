FROM python:3.13-slim

LABEL maintainer="Nathan Grennan <github@cygnusx-1.org>"
LABEL description="Custom Issue Closer GitHub Action"

# Install git (needed for GitHub Actions)
RUN apt-get update && apt-get install -y git && apt-get clean

# Install required Python packages
# RUN pip install --no-cache-dir PyGithub==1.58.2 requests==2.31.0
RUN pip install --no-cache-dir PyGithub==2.6.1 requests==2.32.3

# Set up the working directory
WORKDIR /app

# Copy the Python action script
COPY issue_closer.py /app/issue_closer.py

# Set the entrypoint
ENTRYPOINT ["python", "/app/issue_closer.py"]
