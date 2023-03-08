# Use the official PostgreSQL image as the base image
FROM postgres:13-alpine

# Set the default timezone for the container to UTC
RUN apk add --no-cache tzdata
ENV TZ=UTC

# Expose the PostgreSQL service on port 5432
EXPOSE 5432

# Copy the custom initialization script into the container
COPY init-db.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh
