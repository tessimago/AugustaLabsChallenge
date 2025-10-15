FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application
COPY . .

# Expose port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]