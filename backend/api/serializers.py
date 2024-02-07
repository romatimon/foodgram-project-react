from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers, status
from djoser.serializers import UserCreateSerializer
import base64
from recipes.models import (Tag, Ingredient, Recipe, FavoritRecipe,
                            ShoppingCart, RecipeIngredient)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для работы с изображениями в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserCreateSerializer):
    '''Сериализатор для пользователя.'''
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    '''Сериализатор для создания ингредиентов в рецепте.'''
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientRecipeReadeSerializer(serializers.ModelSerializer):
    '''Сериализатор для чтения ингредиентов в рецепте.'''
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    '''Сериализатор для чтения рецептов.'''
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeReadeSerializer(many=True, read_only=True,
                                                  source='recipeingredients')
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "tags", "author", "ingredients", "is_favorited",
                  "is_in_shopping_cart", "name", "image", "text",
                  "cooking_time")

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return FavoritRecipe.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    '''Сериализатор для создания рецептов.'''
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    ingredients = IngredientRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time')

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент')
        ingredients_list = set()
        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            amount = ingredient.get("amount")
            if amount < 1:
                raise serializers.ValidationError(
                    f"Количество ингредиента не может быть меньше {1}")
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError("Ингредиент не существует")
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    "Ингредиент уже добавлен в рецепт")
            ingredients_list.add(ingredient_id)

        tags = data.get("tags")
        if not tags:
            raise serializers.ValidationError(
                f"Рецепт должен содержать как минимум {1} тег")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги не должны повторяться")

        cooking_time = data.get("cooking_time")
        if cooking_time < 1:
            raise serializers.ValidationError(
                f"Время готовки не может быть менее {1} мин")

        return data

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            ingredients = RecipeIngredient.objects.get_or_create(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )
            print(ingredient)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeReadSerializer(instance,
                                    context=context).data


class RecipeSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода рецептов в SubscriptionSerializer."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptionSerializer(serializers.ModelSerializer):
    '''Сериализатор для подписок.'''
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')

    class Meta:
        model = Subscription
        fields = ("id", "email", "username", "first_name", "last_name",
                  'is_subscribed', 'recipes_count', 'recipes')

    def validate(self, data):
        author = self.context.get('author')
        user = self.context.get('request').user
        if Subscription.objects.filter(
                author=author,
                user=user).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST)
        if user == author:
            raise serializers.ValidationError(
                detail='Невозможно подписаться на себя!',
                code=status.HTTP_400_BAD_REQUEST)
        return data

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=obj.user, author=obj.author).exists()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeSubscriptionSerializer(recipes, many=True).data


class RecipeFavoriteShopSerializer(serializers.ModelSerializer):
    """Cериализатор для списка покупок и избранных рецептов."""
    name = serializers.ReadOnlyField()
    cooking_time = serializers.ReadOnlyField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
