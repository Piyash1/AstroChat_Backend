#!/bin/bash

# Install system dependencies for psycopg2
apt-get update
apt-get install -y libpq-dev gcc python3-dev

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
