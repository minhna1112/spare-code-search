
# Dockerfile for the code search project
# This Dockerfile sets up a Python environment with necessary dependencies for the project.
# Use a slim version of Python 3.11.13 to reduce image size
FROM python:3.11.13-slim-trixie

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src/ /app/src/

WORKDIR /app/src

CMD [ "python", "./runner.py" ]