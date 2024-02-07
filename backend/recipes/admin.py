from django.contrib import admin
from recipes.models import (ShoppingCart, FavoritRecipe, Ingredient, Recipe,
                            RecipeIngredient, Tag)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_count')
    list_filter = ('name', 'author', 'tags')
    inlines = (RecipeIngredientInLine, )

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(FavoritRecipe)
class FavoritRecipeAdmin(admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass
