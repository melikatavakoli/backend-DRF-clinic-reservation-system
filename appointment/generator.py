from datetime import datetime, timedelta, time
from typing import Set

from appointment.models import Appointment


def generate_time_slots(start: time, end: time, slot_minutes: int = 20):
    if not start or not end:
        return []
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while current + timedelta(minutes=slot_minutes) <= end_dt:
        slots.append(current.time().strftime("%H:%M"))
        current += timedelta(minutes=slot_minutes)
    return slots


def get_occupied_slots(doctor, target_date) -> Set[str]:
    occupied = Appointment.objects.filter(
        doctor=doctor,
        date=target_date,
        status__in=['pending', 'checked_in', 'in_progress']
    ).values_list('start_time', flat=True)
    return {t.strftime("%H:%M") for t in occupied if t}


def remove_occupied_slots(slots: list[str], doctor, date) -> list[str]:
    appointments = Appointment.objects.filter(doctor=doctor, date=date)
    reserved = [
        ap.start_time.strftime("%H:%M") for ap in appointments
    ]
    free_slots = [s for s in slots if s in slots and s not in reserved]
    return free_slots
