# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security BEFORE copying packages
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies from builder stage to appuser's local directory
COPY --from=builder /root/.local /home/appuser/.local

# Copy the project files
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY config/ config/
COPY entrypoint.sh .

# Make entrypoint executable and set ownership
RUN chmod +x entrypoint.sh
RUN chown -R appuser:appuser /app /home/appuser/.local

# Switch to non-root user
USER appuser

# Set Python path to include src directory and user packages
ENV PYTHONPATH=/app/src
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose the port FastAPI runs on
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]