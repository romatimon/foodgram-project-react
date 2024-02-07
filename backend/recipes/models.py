from django.contrib.auth import get_user_model
from django.db import models
from colorfield.fields import ColorField

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=100)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=50)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        verbose_name='Название тега',
        unique=True, max_length=200)
    color = ColorField(
        'Цвет тега',
        unique=True)
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=50, unique=True)

    class Meta:
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
        max_length=200,
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
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт {self.name}, автор {self.author}'


class RecipeIngredient(models.Model):
    """Связующая модель для ингредиентов и рецептов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredients')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента')

    class Meta:
        verbose_name = 'количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'


class FavoritRecipe(models.Model):
    """Модель для избранных рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'{self.user}, {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcart',
        verbose_name='Рецепт')

    class Meta:
        verbose_name = "списки покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f'{self.user}, {self.recipe.name}'
