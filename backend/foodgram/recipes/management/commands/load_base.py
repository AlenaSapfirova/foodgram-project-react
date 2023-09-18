from django.core.management.base import BaseCommand
import csv
from recipes.models import Ingredient
from django.conf import settings


class Command(BaseCommand):
    help = 'load base from csv'

    def handle(self, *args, **options):

        with open(f'{settings.BASE_DIR}/data/ingredients.csv',
                  encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                print(row)
                name = row['абрикосовое варенье']
                measurement_unit = row['г']
                ingredient = Ingredient(
                    name=name,
                    measurement_unit=measurement_unit
                )
                ingredient.save()
                line_count += 1
        print(f'Загрузилось {line_count} строк')
