"""
instructors/cost_calculator.py
--------------------------------
Stateless cost calculation logic for instructor batch payouts.

Rules:
  Weekday (Mon–Fri) class day → 2 hours
  Weekend (Sat–Sun) class day → 3 hours
  Cancelled day               → 0 hours (excluded from cost)
  GST                         → cost × gst_percentage / 100  (if applicable)
  Total                       → base_cost + gst_amount
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence


WEEKDAY_HOURS = Decimal('2')
WEEKEND_HOURS = Decimal('3')


def _hours_for_date(d: date) -> Decimal:
    """Return billable hours for a single class date."""
    return WEEKEND_HOURS if d.weekday() >= 5 else WEEKDAY_HOURS


def get_class_dates(
    start: date,
    end: date,
    class_days: str,
) -> list[date]:
    """
    Return all dates between start and end (inclusive) that fall on the
    specified class_days string (e.g. "Mon,Wed,Fri" or "Monday,Wednesday").

    Accepts both abbreviated (Mon) and full (Monday) day names, case-insensitive.
    """
    DAY_MAP = {
        'mon': 0, 'monday': 0,
        'tue': 1, 'tuesday': 1,
        'wed': 2, 'wednesday': 2,
        'thu': 3, 'thursday': 3,
        'fri': 4, 'friday': 4,
        'sat': 5, 'saturday': 5,
        'sun': 6, 'sunday': 6,
    }
    allowed = set()
    for part in class_days.split(','):
        key = part.strip().lower()
        if key in DAY_MAP:
            allowed.add(DAY_MAP[key])

    result = []
    current = start
    while current <= end:
        if current.weekday() in allowed:
            result.append(current)
        current += timedelta(days=1)
    return result


def calculate_batch_cost(
    instructor,
    start: date,
    end: date,
    class_days: str,
    cancelled_dates: Sequence[date],
) -> dict:
    """
    Calculate base cost, GST and total for an instructor over a batch period.

    Args:
        instructor: Instructor model instance.
        start:      Batch start date.
        end:        Batch end date.
        class_days: Comma-separated day names (e.g. "Mon,Wed,Fri").
        cancelled_dates: Iterable of date objects for cancelled sessions.

    Returns:
        {
          'scheduled_days': int,
          'billed_days': int,
          'cancelled_days': int,
          'total_hours': Decimal,
          'cost_per_hour': Decimal,
          'base_cost': Decimal,
          'gst_applicable': bool,
          'gst_percentage': Decimal,
          'gst_amount': Decimal,
          'total_cost': Decimal,
        }
    """
    cancelled_set = set(cancelled_dates)
    all_class_dates = get_class_dates(start, end, class_days)

    total_hours = Decimal('0')
    billed_days = 0

    for d in all_class_dates:
        if d in cancelled_set:
            continue
        total_hours += _hours_for_date(d)
        billed_days += 1

    cost_per_hour = Decimal(str(instructor.cost_per_hour))
    base_cost = (total_hours * cost_per_hour).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    gst_applicable = bool(instructor.gst_applicable)
    gst_percentage = Decimal(str(instructor.gst_percentage)) if gst_applicable else Decimal('0')
    gst_amount = (base_cost * gst_percentage / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if gst_applicable else Decimal('0')
    total_cost = base_cost + gst_amount

    return {
        'scheduled_days': len(all_class_dates),
        'billed_days': billed_days,
        'cancelled_days': len(all_class_dates) - billed_days,
        'total_hours': total_hours,
        'cost_per_hour': cost_per_hour,
        'base_cost': base_cost,
        'gst_applicable': gst_applicable,
        'gst_percentage': gst_percentage,
        'gst_amount': gst_amount,
        'total_cost': total_cost,
    }