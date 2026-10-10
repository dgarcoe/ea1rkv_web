import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.utils import timezone

from ...models import TelegramDelivery
from ...telegram import send_pending


class Command(BaseCommand):
    help = "Procesa la cola de Telegram o consulta su estado"

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true")
        parser.add_argument("--status", action="store_true")
        parser.add_argument("--retry", type=int, metavar="ID")

    def handle(self, *args, **options):
        if options["status"]:
            for row in TelegramDelivery.objects.order_by("-pk")[:100]:
                self.stdout.write(f"{row.pk}: página={row.page_id} {row.status} intentos={row.attempts} mensaje={row.message_id} {row.error}")
            return
        if options["retry"]:
            count = TelegramDelivery.objects.filter(
                pk=options["retry"], status__in=["failed", "uncertain"]
            ).update(status="pending", next_attempt=timezone.now(), attempts=0, error="")
            if not count:
                raise CommandError("No existe un envío fallido o incierto con ese ID")
            self.stdout.write("Reintento encolado. El worker lo enviará.")
            return
        while True:
            close_old_connections()
            try:
                send_pending()
            except ValueError as exc:
                raise CommandError(str(exc)) from None
            if not options["loop"]:
                break
            time.sleep(15)
