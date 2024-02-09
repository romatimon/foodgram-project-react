from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)

from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .filters import IngredientFilter, RecipeFilter
from .paginators import LimitPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import CustomUserSerializer
from users.models import Subscription
from .serializers import (TagSerializer, RecipeFavoriteShopSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          RecipeCreateUpdateSerializer,
                          SubscribeListSerializer)
from recipes.models import (Tag, Ingredient, Recipe, ShoppingCart,
                            FavoritRecipe, RecipeIngredient)


User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователя."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, args, kwargs)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],)
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

        if request.method == 'POST':
            serializer = SubscribeListSerializer(author,
                                                 data=request.data,
                                                 context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if Subscription.objects.filter(user=request.user,
                                           author=author).exists():
                Subscription.objects.filter(user=request.user,
                                            author=author).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeListSerializer(pages,
                                             many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny, )
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        recupe_id = self.kwargs.get('pk')

        if request.method == 'POST':
            if not Recipe.objects.filter(id=recupe_id).exists():
                return Response('Рецепта не существует',
                                status=status.HTTP_400_BAD_REQUEST)

            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            serializer = RecipeFavoriteShopSerializer(
                recipe, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            if not FavoritRecipe.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                FavoritRecipe.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response('Рецепт уже добавлен в избранное.',
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            if FavoritRecipe.objects.filter(user=request.user,
                                            recipe=recipe).exists():
                FavoritRecipe.objects.filter(user=request.user,
                                             recipe=recipe).delete()
                return Response('Рецепт удален',
                                status=status.HTTP_204_NO_CONTENT)
            return Response('Этого рецепта нет в избранном',
                            status=status.HTTP_400_BAD_REQUEST)



















    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, **kwargs):
        recipe_id = self.kwargs.get('pk')

        if request.method == 'POST':
            if not Recipe.objects.filter(id=recipe_id).exists():
                return Response('Такого рецепта не существует',
                                status=status.HTTP_400_BAD_REQUEST)
            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            serializer = RecipeFavoriteShopSerializer(
                recipe, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            if not ShoppingCart.objects.filter(user=request.user,
                                               recipe=recipe).exists():
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response('Рецепт уже добавлен в избранное.',
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            if ShoppingCart.objects.filter(user=request.user,
                                           recipe=recipe).exists():
                ShoppingCart.objects.filter(user=request.user,
                                            recipe=recipe).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)












    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shoppingcart.exists():
            return Response('Ваш список покупок пуст',
                            status=status.HTTP_400_BAD_REQUEST)
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        shoppingcart_list = 'Ваш список покупок'

        shoppingcart_list += '\n'.join([
            f"\u2022 {ingredient['ingredient__name']}"
            f"({ingredient['ingredient__measurement_unit']})"
            f"-- {ingredient['amount']}\n"
            for ingredient in ingredients])

        filename = f'{user.username}_shoppingcart_list.txt'
        response = HttpResponse(
            content=shoppingcart_list,
            content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
