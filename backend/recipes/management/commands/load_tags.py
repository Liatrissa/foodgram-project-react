import csv
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open(
                Path(settings.PATH_DATA, 'tags.csv'),
                encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            Tag.objects.bulk_create(
                Tag(**data) for data in reader)
        self.stdout.write(self.style.SUCCESS('Теги успешно загружены в базу'))
