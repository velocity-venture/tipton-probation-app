"""
TiptonScheduler - Scheduling Logic for Tipton County Probation Voice Agent

Implements office hours, lunch lockout, and appointment validation rules
based on PRD.md specifications.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple, Optional, List
from enum import Enum
import calendar

# Central Time Zone
TZ = ZoneInfo("America/Chicago")


class DayType(Enum):
    """Classification of day types for scheduling."""
    WALK_IN = "walk_in"           # Monday, Wednesday
    COURT_DAY = "court_day"       # Tuesday, Thursday (regular)
    LATE_THURSDAY = "late_thu"    # 1st and 3rd Thursday after-hours
    PHONE_ONLY = "phone_only"     # Friday


class ScheduleResult:
    """Result object for scheduling operations."""
    def __init__(self, allowed: bool, message: str, warning: Optional[str] = None):
        self.allowed = allowed
        self.message = message
        self.warning = warning

    def __repr__(self):
        return f"ScheduleResult(allowed={self.allowed}, message='{self.message}')"


class TiptonScheduler:
    """
    Handles all scheduling logic for Tipton County Probation Office.

    Office Rules:
    - Monday/Wednesday: Walk-in appointments 8:00 AM - 5:00 PM (last slot 4:30 PM)
    - Tuesday/Thursday: Closed to walk-ins (court obligations)
    - Friday: Phone reporting only
    - 1st & 3rd Thursday: After-hours 5:00 PM - 7:30 PM
    - Lunch (Mon/Wed): 12:00 PM - 1:00 PM, must arrive by 11:30 AM
    """

    # Time constants
    OFFICE_OPEN = time(8, 0)
    OFFICE_CLOSE = time(17, 0)
    LAST_APPOINTMENT = time(16, 30)
    LUNCH_START = time(12, 0)
    LUNCH_END = time(13, 0)
    LUNCH_CUTOFF = time(11, 30)
    AFTER_HOURS_START = time(17, 0)
    AFTER_HOURS_END = time(19, 30)

    def __init__(self):
        self.tz = TZ

    def _get_thursday_number(self, dt: datetime) -> int:
        """
        Returns which Thursday of the month this is (1st, 2nd, 3rd, 4th, 5th).
        """
        day = dt.day
        return (day - 1) // 7 + 1

    def _is_late_thursday(self, dt: datetime) -> bool:
        """
        Check if the datetime falls on a 1st or 3rd Thursday.
        """
        if dt.weekday() != 3:  # Thursday = 3
            return False
        thursday_num = self._get_thursday_number(dt)
        return thursday_num in (1, 3)

    def get_day_type(self, dt: datetime) -> DayType:
        """
        Determine what type of day this is for scheduling purposes.

        Args:
            dt: datetime object (should be timezone-aware)

        Returns:
            DayType enum value
        """
        weekday = dt.weekday()

        # Monday (0) or Wednesday (2)
        if weekday in (0, 2):
            return DayType.WALK_IN

        # Friday (4)
        if weekday == 4:
            return DayType.PHONE_ONLY

        # Thursday (3) - check if 1st or 3rd
        if weekday == 3 and self._is_late_thursday(dt):
            return DayType.LATE_THURSDAY

        # Tuesday (1), Thursday (3) regular, Saturday (5), Sunday (6)
        return DayType.COURT_DAY

    def is_office_open(self, dt: datetime) -> ScheduleResult:
        """
        Check if the office is open for walk-in appointments at the given time.

        Enforces:
        - Monday/Wednesday: 8:00 AM - 4:30 PM (last appointment slot)
        - 1st & 3rd Thursday: 5:00 PM - 7:30 PM only
        - Tuesday/Thursday (regular): Closed
        - Friday: Phone only (no walk-ins)

        Args:
            dt: datetime to check (should be timezone-aware)

        Returns:
            ScheduleResult with allowed status and message
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)

        day_type = self.get_day_type(dt)
        current_time = dt.time()

        # Monday/Wednesday - Regular hours
        if day_type == DayType.WALK_IN:
            if current_time < self.OFFICE_OPEN:
                return ScheduleResult(
                    False,
                    f"Office opens at 8:00 AM. Please schedule after that time."
                )
            if current_time > self.LAST_APPOINTMENT:
                return ScheduleResult(
                    False,
                    "The last appointment slot is 4:30 PM. Please choose an earlier time."
                )
            return ScheduleResult(True, "Office is open for walk-in appointments.")

        # 1st & 3rd Thursday - After hours
        if day_type == DayType.LATE_THURSDAY:
            if self.AFTER_HOURS_START <= current_time <= self.AFTER_HOURS_END:
                return ScheduleResult(
                    True,
                    "After-hours appointments available (5:00 PM - 7:30 PM)."
                )
            return ScheduleResult(
                False,
                "After-hours appointments are only from 5:00 PM to 7:30 PM on 1st and 3rd Thursday."
            )

        # Friday - Phone only
        if day_type == DayType.PHONE_ONLY:
            return ScheduleResult(
                False,
                "Fridays are reserved for phone reporting only. No walk-in appointments."
            )

        # Tuesday, regular Thursday, weekends
        return ScheduleResult(
            False,
            "Walk-in appointments are not available on this day due to court obligations. "
            "Please schedule for Monday or Wednesday."
        )

    def check_lunch_lockout(self, dt: datetime) -> ScheduleResult:
        """
        Check if the appointment time falls within the lunch lockout period.

        Lunch Lockout Rules (Monday & Wednesday only):
        - Office closed 12:00 PM - 1:00 PM
        - Must arrive by 11:30 AM to be seen before lunch
        - Times between 11:31 AM and 12:59 PM are REJECTED

        Args:
            dt: datetime to check

        Returns:
            ScheduleResult with rejection status if in lockout period
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)

        day_type = self.get_day_type(dt)
        current_time = dt.time()

        # Lunch lockout only applies to Monday/Wednesday
        if day_type != DayType.WALK_IN:
            return ScheduleResult(True, "Lunch lockout does not apply to this day.")

        # Check if time is in the lockout window (11:31 AM - 12:59 PM)
        if self.LUNCH_CUTOFF < current_time < self.LUNCH_END:
            return ScheduleResult(
                False,
                "LUNCH LOCKOUT: Office is closed from 12:00 PM to 1:00 PM. "
                "To be seen before lunch, you must arrive by 11:30 AM. "
                "Please schedule for 11:30 AM or earlier, or 1:00 PM or later."
            )

        # Warn if close to cutoff
        if time(11, 0) <= current_time <= self.LUNCH_CUTOFF:
            return ScheduleResult(
                True,
                "Appointment scheduled.",
                warning="Note: Office closes for lunch at 12:00 PM. Arrive by 11:30 AM to be seen before lunch."
            )

        return ScheduleResult(True, "No lunch lockout conflict.")

    def get_friday_instruction(self) -> str:
        """
        Returns the instruction message for Friday phone reporting.

        Returns:
            String with phone reporting instructions
        """
        return (
            "Phone reporting is active. Fridays are reserved for phone check-ins only. "
            "Please leave a message or complete your phone report now. "
            "No in-person appointments are available on Fridays."
        )

    def format_payment_msg(self) -> str:
        """
        Returns the standardized payment information message.

        Returns:
            String with payment policy information
        """
        return (
            "Payments are CASH ONLY ($75) and collected at the time of your appointment. "
            "However, you are NOT required to have payment in order to be seen. "
            "Please report regardless of your ability to pay."
        )

    def get_missed_appointment_options(self, dt: datetime) -> ScheduleResult:
        """
        Returns available rescheduling options for missed appointments.

        Missed appointments can ONLY be rescheduled for Monday or Wednesday
        before the end of the current month. Late Thursday is NOT an option.

        Args:
            dt: Current datetime

        Returns:
            ScheduleResult with available options
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.tz)

        # Get remaining Mondays and Wednesdays in the month
        year = dt.year
        month = dt.month
        _, last_day = calendar.monthrange(year, month)

        available_dates = []
        current_day = dt.day

        for day in range(current_day + 1, last_day + 1):
            check_date = datetime(year, month, day, tzinfo=self.tz)
            if check_date.weekday() in (0, 2):  # Monday or Wednesday only
                available_dates.append(check_date.strftime("%A, %B %d"))

        if not available_dates:
            return ScheduleResult(
                False,
                "No available Monday or Wednesday slots remain this month. "
                "Please contact the office to schedule for next month."
            )

        dates_str = ", ".join(available_dates[:5])  # Show up to 5 options
        return ScheduleResult(
            True,
            f"You have a missed appointment. You can reschedule for: {dates_str}. "
            "Please note: Missed appointments must be rescheduled for Monday or Wednesday only."
        )

    def validate_appointment(self, dt: datetime) -> ScheduleResult:
        """
        Full validation of an appointment datetime.

        Runs all checks: office hours, lunch lockout, day type.

        Args:
            dt: Proposed appointment datetime

        Returns:
            ScheduleResult with final validation status
        """
        # Check if office is open
        office_check = self.is_office_open(dt)
        if not office_check.allowed:
            return office_check

        # Check lunch lockout (only affects Mon/Wed)
        lunch_check = self.check_lunch_lockout(dt)
        if not lunch_check.allowed:
            return lunch_check

        # All checks passed
        return ScheduleResult(
            True,
            "Appointment time is valid.",
            warning=lunch_check.warning
        )
