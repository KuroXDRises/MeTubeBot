# Base image
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# System deps for pillow + telegram crypto

# Copy project files
COPY . .

# Upgrade pip first
RUN apt-get update && apt-get install -y
RUN pip3 install --upgrade pip setuptools wheel
# Install requirements
RUN pip3 install -r requirements.txt

# Expose port (Optional)
EXPOSE 8080

# Run bot (Make sure your main file is bot.py)
CMD ["python", "bot.py"]
