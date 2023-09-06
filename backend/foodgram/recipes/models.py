from django.db import models
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator
)

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        unique=True,
        max_length=200,
        blank=False,
    )
    color = models.CharField(
        max_length=16,
        unique=True,
        blank=False
    )
    slug = models.SlugField(
        null=True,
        unique=True,
        validators=[RegexValidator(regex=r'^[-a-zA-Z0-9_]+$')],
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    name = models.CharField(
        max_length=254,
        blank=False
    )
    measurement_unit = models.CharField(
        max_length=10
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredients'
            ),
        )

    def __str__(self):
        return self.name


class Recipes(models.Model):
    name = models. CharField(
        max_length=100,
        blank=False,
        verbose_name='Название'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tag'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        blank=False,
        verbose_name='Автор'
    )
    image = models.ImageField(
        upload_to='recipes/images/%Y/%m/%D/',
        verbose_name='Загрузить фото',
        null=True,
        default=None
    )
    text = models.TextField(blank=False, verbose_name='Описание')
    cooking_time = models.SmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(1200)
        ],
        blank=False,
        verbose_name='Время приготовления'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='Amount',
        verbose_name='Ингредиенты'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Рецепты'
        verbose_name = 'Рецепт'

    def __str__(self):
        return self.name


class Amount(models.Model):
    amount = models.SmallIntegerField(
        default=1,
        validators=[MinValueValidator(1),
                    MaxValueValidator(1000)]
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='recipe'
    )


class FavoriteBase(models.Model):
    recipes = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_recipes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_user'
    )

    class Meta:
        abstract = True


class Shopping_Cart(FavoriteBase):
    class Meta:
        db_table = 'Shopping_Cart'
        verbose_name = 'Список покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_shopping_cart_recipe')
        ]


class Favorite(FavoriteBase):
    class Meta:
        db_table = 'Favorite'
        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_favorite_recipe')

        ]
