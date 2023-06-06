import csv
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка из csv файла'

    def handle(self, *args, **kwargs):
        with open(
                Path(settings.PATH_DATA, 'ingredients.csv'),
                encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in reader)
        self.stdout.write(
            self.style.SUCCESS('Ингредиенты успешно загружены в базу'))
