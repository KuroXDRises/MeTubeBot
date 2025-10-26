# Base image
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Expose port (optional, for webhooks if needed)
EXPOSE 8080
# Run bot
CMD ["python", "setup.py"]
