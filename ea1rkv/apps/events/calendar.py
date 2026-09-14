"""Shared activity listing and monthly calendar, without duplicating pages."""
import calendar
from datetime import date

from django.utils import timezone
from django.utils.translation import gettext as _


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
    items.sort(key=lambda item: (item.start_date, item.pk))
    past = request.GET.get("past") == "true"
    listing = [item for item in items if ((item.end_date or item.start_date) < today) == past]
    if past:
        listing.reverse()
    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month):
        weeks.append([{
            "date": day, "current": day.month == month.month, "today": day == today,
            "items": [item for item in items if item.start_date <= day <= (item.end_date or item.start_date)],
        } for day in week])
    previous = date(month.year - (month.month == 1), 12 if month.month == 1 else month.month - 1, 1)
    following = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
    return {"events": listing, "show_past": past, "event_types": types,
            "selected_type": selected, "calendar_weeks": weeks, "calendar_month": month,
            "previous_month": previous.strftime("%Y-%m"), "next_month": following.strftime("%Y-%m"),
            "weekdays": [_("Lunes"), _("Martes"), _("Miércoles"), _("Jueves"), _("Viernes"), _("Sábado"), _("Domingo")]}
