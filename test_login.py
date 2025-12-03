"""Test if login tracking is working"""
import sys
sys.path.insert(0, '/Users/chris/juergen')

print("=== STARTING TEST ===")

# Test 1: Import streamlit
print("Test 1: Importing streamlit...")
import streamlit as st
print("✓ Streamlit imported successfully")

# Test 2: Check if secrets file exists
print("\nTest 2: Checking secrets file...")
import os
secrets_path = "/Users/chris/juergen/.streamlit/secrets.toml"
if os.path.exists(secrets_path):
    print(f"✓ Secrets file exists at {secrets_path}")
    with open(secrets_path, 'r') as f:
        content = f.read()
        if '[gsheet_credentials]' in content:
            print("✓ Found [gsheet_credentials] section")
        if 'login_sheet_url' in content:
            print("✓ Found login_sheet_url")
else:
    print(f"✗ Secrets file NOT found at {secrets_path}")

# Test 3: Try to load secrets (requires streamlit to be running)
print("\nTest 3: This test requires Streamlit to be running")
print("The actual secrets test will happen when you run the app")

print("\n=== TEST COMPLETE ===")
