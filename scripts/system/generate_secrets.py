#!/usr/bin/env python3
"""
Generate secure secrets for .env file
Usage: python generate_secrets.py >> .env
"""

import secrets
import sys

def generate_strong_password(length=32):
    """Generate a cryptographically strong password"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_url_safe_token(length=32):
    """Generate a URL-safe token suitable for SECRET_KEY and JWT_SECRET"""
    return secrets.token_urlsafe(length)

def main():
    """Generate all required secrets"""
    print("# Generated Secrets - DO NOT COMMIT THIS FILE")
    print("# Add these to your .env file")
    print()
    print(f"# PostgreSQL Password (generated)")
    print(f"POSTGRES_PASSWORD={generate_strong_password()}")
    print()
    print(f"# Flask Secret Key (generated)")
    print(f"SECRET_KEY={generate_url_safe_token()}")
    print()
    print(f"# JWT Secret (generated)")
    print(f"JWT_SECRET={generate_url_safe_token()}")
    print()
    print(f"# Optional: Redis Password (generated)")
    print(f"# REDIS_PASSWORD={generate_strong_password()}")
    print()
    print("# IMPORTANT: Copy these values to your .env file")
    print("# Never commit the .env file to version control!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        print("\nExamples:")
        print("  python generate_secrets.py               # Print to console")
        print("  python generate_secrets.py > secrets.txt # Save to file")
        print("  python generate_secrets.py >> .env       # Append to .env (careful!)")
        sys.exit(0)
    
    main()
