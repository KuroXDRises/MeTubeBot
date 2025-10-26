# Base image
FROM python:3.12-slim
# Set workdir
WORKDIR /app
# Copy bot code
COPY . .
#RUN
RUN pip3 install -U -r requirements.txt
# Expose port (optional, for webhooks if needed)
EXPOSE 8080
# Run bot
CMD ["python", "setup.py"]
