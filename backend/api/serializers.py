import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers, status
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Ingredient, FavoritRecipe, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
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
    """Сериализатор для пользователя."""
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
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class IngredientRecipeReadeSerializer(serializers.ModelSerializer):
    '''Сериализатор для чтения ингредиентов в рецепте.'''
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
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
        request = self.context.get('request')
        return request.user.is_authenticated and FavoritRecipe.objects.filter(
            user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return request.user.is_authenticated and ShoppingCart.objects.filter(
            user=request.user, recipe=obj).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    '''Сериализатор для создания рецептов.'''
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    ingredients = IngredientRecipeCreateSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

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
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError("Ингредиент не существует")
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    "Ингредиент уже добавлен в рецепт")
            ingredients_list.add(ingredient_id)
        tags = data.get("tags")
        if not tags:
            raise serializers.ValidationError(
                "Рецепт должен содержать как минимум 1 тег")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError("Теги не должны повторяться")

        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),)
            for ingredient in ingredients)

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
    """Сериализатор для вывода рецептов в SubscribeListSerializer."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscribeListSerializer(CustomUserSerializer):
    """Сериализатор для просмотра подписок."""
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes_count',
                                                     'recipes')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscription.objects.filter(author=author, user=user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя',
                status.HTTP_400_BAD_REQUEST)
        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя',
                status.HTTP_400_BAD_REQUEST)
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        serializer = RecipeSubscriptionSerializer(recipes, many=True,
                                                  read_only=True)
        return serializer.data


class RecipeFavoriteShopSerializer(serializers.ModelSerializer):
    """Cериализатор для списка покупок и избранных рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка покупок. """
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок.'
            )
        ]

    def to_representation(self, instance):
        return RecipeFavoriteShopSerializer(instance.recipe, context={
            'request': self.context.get('request')}).data


class FavoriteSerializer(serializers.ModelSerializer):
    """ Сериализатор модели Избранное. """
    class Meta:
        model = FavoritRecipe
        fields = ('user', 'recipe')

        validators = [
            UniqueTogetherValidator(
                queryset=FavoritRecipe.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное.'
            )
        ]

    def to_representation(self, instance):
        return RecipeFavoriteShopSerializer(instance.recipe, context={
            'request': self.context.get('request')}).data
