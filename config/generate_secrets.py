#!/usr/bin/env python3
"""
Generate secure secrets for configuration.

Usage:
    python config/generate_secrets.py

Output can be appended to .env:
    python config/generate_secrets.py >> .env
"""

import secrets


def generate_secret_key(length: int = 32) -> str:
    """Generate a random hex secret key"""
    return secrets.token_hex(length)


def generate_jwt_secret(length: int = 32) -> str:
    """Generate a random JWT secret"""
    return secrets.token_urlsafe(length)


def main():
    print("# Generated secrets - Add these to your .env file")
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"JWT_SECRET={generate_jwt_secret()}")
    
    # Generate Redis password if needed
    print(f"# REDIS_PASSWORD={generate_secret_key(16)}  # Uncomment if using Redis auth")
    
    # Generate PostgreSQL password if needed
    print(f"# POSTGRES_PASSWORD={generate_secret_key(16)}  # Uncomment if using PostgreSQL")


if __name__ == "__main__":
    main()
