from django.core.management import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Создаем тэги'

    def handle(self, *args, **kwargs):
        data = [
            {'name': 'Завтрак', 'color': '#1745b4', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#1c9b5d', 'slug': 'dinner'},
            {'name': 'Ужин', 'color': '#8f6c1e', 'slug': 'supper'},
            {'name': 'Напитки', 'color': '#8f6c1e', 'slug': 'drinks'},
            {'name': 'Десерт', 'color': '#7222bc', 'slug': 'dessert'}]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        self.stdout.write(self.style.SUCCESS('Все тэги загружены!'))
