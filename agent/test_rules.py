#!/usr/bin/env python3
"""
Test Suite for TiptonScheduler Business Rules

Tests the core scheduling logic per PRD.md requirements:
1. Lunch Lockout enforcement (11:30 AM - 1:00 PM on Mon/Wed)
2. Friday phone reporting
3. Missed appointment rescheduling (Mon/Wed only, NOT Late Thursday)
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from tipton_scheduler import TiptonScheduler, DayType

TZ = ZoneInfo("America/Chicago")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print formatted test result."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"       {details}")
    print()


def test_lunch_lockout_1145():
    """
    Test 1: User arrives Monday 11:45 AM -> REJECT (Lunch Lockout)

    11:45 AM is after the 11:30 AM cutoff but before lunch at 12:00 PM.
    This should be REJECTED because they won't be seen before lunch closes.
    """
    scheduler = TiptonScheduler()

    # Monday, January 20, 2025 at 11:45 AM Central
    dt = datetime(2025, 1, 20, 11, 45, tzinfo=TZ)

    result = scheduler.check_lunch_lockout(dt)

    # Should be rejected (allowed = False)
    passed = result.allowed == False and "LUNCH LOCKOUT" in result.message

    print_result(
        "Test 1: Monday 11:45 AM -> REJECT (Lunch Lockout)",
        passed,
        f"allowed={result.allowed}, message='{result.message[:60]}...'"
    )
    return passed


def test_lunch_lockout_1230():
    """
    Test 2: User arrives Monday 12:30 PM -> REJECT (During Lunch)

    12:30 PM is during lunch hours (12:00 PM - 1:00 PM).
    This should be REJECTED.
    """
    scheduler = TiptonScheduler()

    # Monday, January 20, 2025 at 12:30 PM Central
    dt = datetime(2025, 1, 20, 12, 30, tzinfo=TZ)

    result = scheduler.check_lunch_lockout(dt)

    # Should be rejected (allowed = False)
    passed = result.allowed == False and "LUNCH LOCKOUT" in result.message

    print_result(
        "Test 2: Monday 12:30 PM -> REJECT (Lunch Period)",
        passed,
        f"allowed={result.allowed}, message='{result.message[:60]}...'"
    )
    return passed


def test_friday_phone_instruction():
    """
    Test 3: User calls Friday -> RETURN 'Phone Report' instruction

    Fridays are phone reporting only. Should return the phone reporting message.
    """
    scheduler = TiptonScheduler()

    # Friday, January 24, 2025 at 10:00 AM Central
    dt = datetime(2025, 1, 24, 10, 0, tzinfo=TZ)

    # Check day type
    day_type = scheduler.get_day_type(dt)

    # Get Friday instruction
    instruction = scheduler.get_friday_instruction()

    # Also check is_office_open rejects walk-ins
    office_result = scheduler.is_office_open(dt)

    passed = (
        day_type == DayType.PHONE_ONLY and
        "phone" in instruction.lower() and
        office_result.allowed == False and
        "phone reporting" in office_result.message.lower()
    )

    print_result(
        "Test 3: Friday -> RETURN 'Phone Report' instruction",
        passed,
        f"day_type={day_type.value}, instruction='{instruction[:50]}...'"
    )
    return passed


def test_missed_appointment_options():
    """
    Test 4: Missed Appointment -> RETURN Mon/Wed options (NOT Late Thursday)

    A user with a missed appointment should only be offered Monday or Wednesday
    slots. Late Thursday should NOT be an option.
    """
    scheduler = TiptonScheduler()

    # Current date: Monday, January 20, 2025
    dt = datetime(2025, 1, 20, 9, 0, tzinfo=TZ)

    result = scheduler.get_missed_appointment_options(dt)

    # Check that options are provided
    has_options = result.allowed and "Monday" in result.message or "Wednesday" in result.message

    # Check that Thursday is NOT mentioned as an option
    no_thursday = "Thursday" not in result.message

    # Check the note about Mon/Wed only
    correct_note = "Monday or Wednesday only" in result.message

    passed = has_options and no_thursday and correct_note

    print_result(
        "Test 4: Missed Appt -> Mon/Wed options only (NOT Late Thu)",
        passed,
        f"allowed={result.allowed}, has_mon_wed={has_options}, no_thursday={no_thursday}"
    )
    return passed


def test_late_thursday_detection():
    """
    Bonus Test: Verify 1st and 3rd Thursday detection works correctly.
    """
    scheduler = TiptonScheduler()

    # 1st Thursday of January 2025 = January 2nd
    first_thu = datetime(2025, 1, 2, 18, 0, tzinfo=TZ)

    # 2nd Thursday of January 2025 = January 9th
    second_thu = datetime(2025, 1, 9, 18, 0, tzinfo=TZ)

    # 3rd Thursday of January 2025 = January 16th
    third_thu = datetime(2025, 1, 16, 18, 0, tzinfo=TZ)

    first_is_late = scheduler.get_day_type(first_thu) == DayType.LATE_THURSDAY
    second_is_court = scheduler.get_day_type(second_thu) == DayType.COURT_DAY
    third_is_late = scheduler.get_day_type(third_thu) == DayType.LATE_THURSDAY

    passed = first_is_late and second_is_court and third_is_late

    print_result(
        "Bonus: Late Thursday Detection (1st & 3rd only)",
        passed,
        f"1st={first_is_late}, 2nd={second_is_court}, 3rd={third_is_late}"
    )
    return passed


def test_payment_message():
    """
    Bonus Test: Verify payment message contains required information.
    """
    scheduler = TiptonScheduler()

    msg = scheduler.format_payment_msg()

    has_cash = "CASH ONLY" in msg.upper()
    has_amount = "$75" in msg
    has_not_required = "NOT required" in msg or "not required" in msg.lower()

    passed = has_cash and has_amount and has_not_required

    print_result(
        "Bonus: Payment Message Format",
        passed,
        f"cash={has_cash}, amount={has_amount}, not_required={has_not_required}"
    )
    return passed


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("TIPTON SCHEDULER - BUSINESS RULES TEST SUITE")
    print("=" * 60)
    print()

    results = []

    # Core tests (required)
    results.append(("Test 1: Lunch Lockout 11:45 AM", test_lunch_lockout_1145()))
    results.append(("Test 2: Lunch Lockout 12:30 PM", test_lunch_lockout_1230()))
    results.append(("Test 3: Friday Phone Instruction", test_friday_phone_instruction()))
    results.append(("Test 4: Missed Appt Mon/Wed Only", test_missed_appointment_options()))

    # Bonus tests
    results.append(("Bonus: Late Thursday Detection", test_late_thursday_detection()))
    results.append(("Bonus: Payment Message", test_payment_message()))

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")

    print()
    print(f"Results: {passed_count}/{total_count} tests passed")
    print()

    if passed_count == total_count:
        print("ALL TESTS PASSED")
        return 0
    else:
        print("SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
