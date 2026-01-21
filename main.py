#!/usr/bin/env python3
"""
Tipton Probation Voice Agent - Simulation Runner

A text-based simulation of the voice agent for testing scheduling logic.
Connects to Supabase to lookup callers and uses TiptonScheduler for business rules.
"""

import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add agent module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from supabase import create_client, Client
from tipton_scheduler import TiptonScheduler, DayType

# Timezone
TZ = ZoneInfo("America/Chicago")

# Supabase credentials
SUPABASE_URL = "https://fgoyvskkrmdzkghztrbc.supabase.co"
SUPABASE_KEY = "sb_secret_Apn_ADTRzBGcKHbYfR3Rdw_HxP1Q_pr"

# Office contact for escalation
OFFICE_PHONE = "(901) 555-0199"


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def lookup_caller(supabase: Client, phone_number: str) -> dict | None:
    """
    Lookup a probationer by phone number.

    Args:
        supabase: Supabase client
        phone_number: Caller's phone number

    Returns:
        Probationer record dict or None if not found
    """
    try:
        response = supabase.table("probationers").select("*").eq(
            "phone_number", phone_number
        ).eq("is_active", True).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"[ERROR] Database lookup failed: {e}")
        return None


def get_appointments(supabase: Client, probationer_id: str) -> list:
    """
    Get appointments for a probationer.

    Args:
        supabase: Supabase client
        probationer_id: UUID of the probationer

    Returns:
        List of appointment records
    """
    try:
        response = supabase.table("appointments").select("*").eq(
            "probationer_id", probationer_id
        ).order("scheduled_time", desc=True).execute()

        return response.data or []
    except Exception as e:
        print(f"[ERROR] Failed to fetch appointments: {e}")
        return []


def parse_datetime(dt_string: str) -> datetime | None:
    """
    Parse a datetime string in format 'YYYY-MM-DD HH:MM'.

    Args:
        dt_string: Datetime string to parse

    Returns:
        datetime object with Central timezone or None if invalid
    """
    try:
        dt = datetime.strptime(dt_string.strip(), "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=TZ)
    except ValueError:
        return None


def print_header():
    """Print the simulation header."""
    print()
    print("=" * 60)
    print("  TIPTON COUNTY PROBATION - VOICE AGENT SIMULATOR")
    print("=" * 60)
    print()


def print_agent_response(message: str, is_warning: bool = False):
    """Print a formatted agent response."""
    prefix = "[WARNING]" if is_warning else "[AGENT]"
    print()
    print(f"  {prefix}")
    # Word wrap the message
    words = message.split()
    line = "    "
    for word in words:
        if len(line) + len(word) > 58:
            print(line)
            line = "    " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)
    print()


def simulate_call(supabase: Client, scheduler: TiptonScheduler):
    """
    Simulate a single phone call interaction.

    Args:
        supabase: Supabase client
        scheduler: TiptonScheduler instance
    """
    print("-" * 60)
    print("  INCOMING CALL...")
    print("-" * 60)

    # Get phone number
    phone = input("\n  Enter Phone Number (or 'quit'): ").strip()

    if phone.lower() in ('quit', 'exit', 'q'):
        return False

    # Lookup caller
    print(f"\n  [SYSTEM] Looking up caller: {phone}")
    caller = lookup_caller(supabase, phone)

    if not caller:
        print_agent_response(
            f"UNKNOWN CALLER. I'm sorry, I wasn't able to find your record "
            f"with this phone number. Please call our office directly at "
            f"{OFFICE_PHONE} for assistance. Our hours are Monday and Wednesday, "
            f"8 AM to 5 PM."
        )
        return True

    # Caller found - greet them
    name = caller.get('full_name', 'Unknown')
    case_number = caller.get('case_number', 'N/A')
    risk_level = caller.get('risk_level', 'Unknown')

    print()
    print(f"  [SYSTEM] Caller identified:")
    print(f"    Name:        {name}")
    print(f"    Case #:      {case_number}")
    print(f"    Risk Level:  {risk_level}")

    print_agent_response(
        f"Hello {name.split()[0]}! Thank you for calling Tipton County Probation. "
        f"I have your record on file. How can I help you today?"
    )

    # Get simulated datetime
    print("  Simulate Date/Time? (YYYY-MM-DD HH:MM)")
    dt_input = input("  Press Enter for NOW, or enter date: ").strip()

    if dt_input:
        sim_dt = parse_datetime(dt_input)
        if not sim_dt:
            print("  [ERROR] Invalid format. Using current time.")
            sim_dt = datetime.now(TZ)
    else:
        sim_dt = datetime.now(TZ)

    # Display simulated time
    day_name = sim_dt.strftime("%A")
    time_str = sim_dt.strftime("%I:%M %p")
    date_str = sim_dt.strftime("%B %d, %Y")

    print()
    print(f"  [SIMULATION] {day_name}, {date_str} at {time_str}")
    print()

    # Get day type
    day_type = scheduler.get_day_type(sim_dt)

    # Check appointments
    appointments = get_appointments(supabase, caller['id'])
    has_missed = any(a.get('status') == 'Missed' for a in appointments)
    scheduled = [a for a in appointments if a.get('status') == 'Scheduled']

    # Process based on day type and rules
    if day_type == DayType.PHONE_ONLY:
        # Friday - Phone reporting
        print_agent_response(scheduler.get_friday_instruction())
        if scheduled:
            print_agent_response(
                "I'm marking your phone check-in as complete. Thank you for reporting."
            )
    else:
        # Check if office is open
        office_result = scheduler.is_office_open(sim_dt)

        if not office_result.allowed:
            print_agent_response(office_result.message)
        else:
            # Check lunch lockout
            lunch_result = scheduler.check_lunch_lockout(sim_dt)

            if not lunch_result.allowed:
                print_agent_response(lunch_result.message)
            else:
                # Office is open and no lockout
                print_agent_response(office_result.message)

                if lunch_result.warning:
                    print_agent_response(lunch_result.warning, is_warning=True)

                # Show next appointment if exists
                if scheduled:
                    next_appt = scheduled[0]
                    appt_time = next_appt.get('scheduled_time', '')
                    if appt_time:
                        try:
                            appt_dt = datetime.fromisoformat(appt_time.replace('Z', '+00:00'))
                            appt_str = appt_dt.strftime("%A, %B %d at %I:%M %p")
                            print_agent_response(
                                f"You have an upcoming appointment scheduled for {appt_str}."
                            )
                        except:
                            pass

                # Check for missed appointments
                if has_missed:
                    missed_options = scheduler.get_missed_appointment_options(sim_dt)
                    print_agent_response(missed_options.message, is_warning=True)

    # Offer payment info
    print("  Would you like payment information? (y/n): ", end="")
    if input().strip().lower() == 'y':
        print_agent_response(scheduler.format_payment_msg())

    print()
    return True


def main():
    """Main entry point for the simulation."""
    print_header()

    # Initialize
    print("  [SYSTEM] Initializing Supabase connection...")
    supabase = get_supabase_client()
    scheduler = TiptonScheduler()
    print("  [SYSTEM] Ready.\n")

    # Main loop
    running = True
    while running:
        try:
            running = simulate_call(supabase, scheduler)
        except KeyboardInterrupt:
            print("\n\n  [SYSTEM] Interrupted by user.")
            running = False
        except Exception as e:
            print(f"\n  [ERROR] Unexpected error: {e}")
            running = True

    print()
    print("=" * 60)
    print("  SIMULATION ENDED")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
