#!/bin/bash

psql -U "$POSTGRES_USER" -c "CREATE DATABASE \"$POSTGRES_DB_NAME\";"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB_NAME" -c "CREATE TABLE \"$POSTGRES_USERS_TABLE_NAME\" (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    verified BOOLEAN DEFAULT false,
    activation_code SMALLINT NOT NULL,
    activation_code_created_at TIMESTAMP NOT NULL
);"
