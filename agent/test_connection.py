#!/usr/bin/env python3
"""
Supabase Connection Test Script
Tests connection to Tipton Probation database and fetches probationer data.
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Supabase credentials from .env.local
SUPABASE_URL = "https://fgoyvskkrmdzkghztrbc.supabase.co"
SUPABASE_KEY = "sb_secret_Apn_ADTRzBGcKHbYfR3Rdw_HxP1Q_pr"

def main():
    try:
        from supabase import create_client, Client
    except ImportError:
        print("ERROR: supabase package not installed. Run: pip install supabase")
        sys.exit(1)

    print("Initializing Supabase client...")

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Client initialized successfully.")
    except Exception as e:
        print(f"ERROR initializing client: {e}")
        sys.exit(1)

    print("\nQuerying 'probationers' table...")

    try:
        response = supabase.table("probationers").select("*").execute()

        if response.data:
            print(f"\n[OK] Found {len(response.data)} probationer(s):\n")
            for p in response.data:
                print(f"  Case #: {p.get('case_number', 'N/A')}")
                print(f"  Name:   {p.get('full_name', 'N/A')}")
                print(f"  Risk:   {p.get('risk_level', 'N/A')}")
                print(f"  Phone:  {p.get('phone_number', 'N/A')}")
                print(f"  Active: {p.get('is_active', 'N/A')}")
                print("-" * 40)

            # Check for John Doe specifically
            john_doe = next((p for p in response.data if "John" in str(p.get('full_name', '')) or "Doe" in str(p.get('full_name', ''))), None)
            if john_doe:
                print(f"\nCONNECTION SUCCESSFUL: Found John Doe")
            else:
                print(f"\nCONNECTION SUCCESSFUL: Data retrieved (John Doe not in current dataset)")
        else:
            print("Query executed but no data returned.")
            print("Table may be empty or RLS policies may be blocking access.")

    except Exception as e:
        print(f"ERROR querying table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
