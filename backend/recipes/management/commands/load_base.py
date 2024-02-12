import csv

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из файла data/ingredients.csv'

    def handle(self, *args, **options):
        with open('data/ingredients.csv', 'r',
                  encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            created_count = 0
            for row in reader:
                name, unit = row
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name, measurement_unit=unit)
                if created:
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Добавлено {created_count} ингредиентов'
                )
            )
