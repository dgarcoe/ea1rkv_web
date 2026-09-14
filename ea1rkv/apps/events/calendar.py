"""Shared activity listing and monthly calendar, without duplicating pages."""
import calendar
import copy
from datetime import date, timedelta

from django.utils import timezone
from django.utils.translation import gettext as _


def occurrence_dates(item, start, end):
    """Return occurrences intersecting [start, end], including recurring events."""
    if getattr(item, "recurrence", "none") == "none":
        first = max(start, item.start_date)
        last = min(end, item.end_date or item.start_date)
        return [first + timedelta(days=n) for n in range((last - first).days + 1)] if first <= last else []
    result = []
    month = start.replace(day=1)
    while month <= end:
        weeks = calendar.monthcalendar(month.year, month.month)
        rows = [week for week in weeks if week[item.recurrence_weekday]]
        day_number = rows[-1][item.recurrence_weekday] if item.recurrence_week == 5 else rows[item.recurrence_week - 1][item.recurrence_weekday]
        occurrence = month.replace(day=day_number)
        if occurrence >= item.start_date and (not item.recurrence_until or occurrence <= item.recurrence_until) and start <= occurrence <= end:
            result.append(occurrence)
        month = (month.replace(year=month.year + 1, month=1) if month.month == 12 else month.replace(month=month.month + 1))
    return result


def occurrence(item, day):
    copy_item = copy.copy(item)
    copy_item.source_start_date = item.start_date
    copy_item.occurrence_date = day
    if getattr(item, "recurrence", "none") != "none":
        copy_item.start_date = day
        copy_item.end_date = day
    return copy_item


def agenda_context(page, request):
    from ea1rkv.apps.club.models import SpecialCallsignPage
    from ea1rkv.apps.events.models import EventPage, EventType

    today = timezone.localdate()
    try:
        month = date.fromisoformat(request.GET.get("month", today.strftime("%Y-%m")) + "-01")
        if not 1900 <= month.year <= 2100:
            raise ValueError
    except ValueError:
        month = today.replace(day=1)
    selected = request.GET.get("type", "")
    types = list(EventType.choices) + [("callsign", _("Indicativos especiales"))]
    if selected not in dict(types):
        selected = ""
    items = list(EventPage.objects.child_of(page).live().public())
    specials = SpecialCallsignPage.objects.descendant_of(page.get_parent()).live().public().filter(
        locale_id=page.locale_id, start_date__isnull=False
    )
    for item in specials:
        item.event_type = "callsign"
        item.agenda_label = _("Indicativos especiales")
        items.append(item)
    items = [item for item in items if not selected or item.event_type == selected]
    horizon = date(today.year + 1, today.month, today.day)
    expanded = [occurrence(item, day) for item in items for day in occurrence_dates(item, today - timedelta(days=365), horizon)]
    items = expanded
    # Show each page once in the list; the calendar still receives every day.
    unique = {}
    for item in items:
        unique.setdefault(item.pk, item)
    listing_items = list(unique.values())
    past = request.GET.get("past") == "true"
    listing = [item for item in listing_items if ((item.end_date or item.start_date) < today) == past]
    if past:
        listing.reverse()
    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month):
        weeks.append([{
            "date": day, "current": day.month == month.month, "today": day == today,
            "items": [item for item in items if item.occurrence_date == day],
        } for day in week])
    previous = date(month.year - (month.month == 1), 12 if month.month == 1 else month.month - 1, 1)
    following = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
    return {"events": listing, "show_past": past, "event_types": types,
            "selected_type": selected, "calendar_weeks": weeks, "calendar_month": month,
            "previous_month": previous.strftime("%Y-%m"), "next_month": following.strftime("%Y-%m"),
            "weekdays": [_("Lunes"), _("Martes"), _("Miércoles"), _("Jueves"), _("Viernes"), _("Sábado"), _("Domingo")]}
