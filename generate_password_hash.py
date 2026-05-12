"""
Generate password hashes for the portfolio app.

Run:
    python3 generate_password_hash.py annika
"""

from __future__ import annotations

import argparse
import getpass

from security import hash_password


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Streamlit secrets password hash.")
    parser.add_argument("username", help="Portfolio username")
    args = parser.parse_args()

    password = getpass.getpass(f"New password for {args.username}: ")
    confirmation = getpass.getpass("Confirm password: ")

    if password != confirmation:
        print("Passwords do not match.")
        return 1

    password_hash = hash_password(password)
    username = args.username.strip().lower()

    print("\nAdd this to .streamlit/secrets.toml or Streamlit Cloud secrets:\n")
    print("[password_hashes]")
    print(f'{username} = "{password_hash}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
