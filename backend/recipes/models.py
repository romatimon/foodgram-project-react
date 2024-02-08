from colorfield.fields import ColorField

from django.db import models
from django.core import validators

from users.models import User

MAX_LENGTH = 100


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=MAX_LENGTH)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_LENGTH)

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit')]

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        verbose_name='Название тега',
        unique=True, max_length=MAX_LENGTH)
    color = ColorField(
        'Цвет тега',
        unique=True)
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=MAX_LENGTH, unique=True)

    class Meta:
        ordering = ('id',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта')
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название рецепта')
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение рецепта')
    text = models.TextField(
        verbose_name='Описание рецепта')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации")
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[validators.MinValueValidator(
            1, message='Минимальное время приголовления 1 минута.')])

    class Meta:
        ordering = ('name',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт {self.name}, автор {self.author}'


class RecipeIngredient(models.Model):
    """Связующая модель ингредиентов и рецептов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredients')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        validators=[validators.MinValueValidator(
            1, message='Минимальное количество ингредиентов - 1')])

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipeingredients')]


class AbstractFavoritShoppingCart(models.Model):
    """Абстрактная базовая модель покупок и избранных рцептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user}, {self.recipe.name}'


class FavoritRecipe(AbstractFavoritShoppingCart):
    """Модель избранных рецептов."""

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorites')]


class ShoppingCart(AbstractFavoritShoppingCart):
    """Модель списка покупок."""

    class Meta:
        verbose_name = "списки покупок"
        verbose_name_plural = "Списки покупок"
        default_related_name = 'shoppingcart'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart')]
