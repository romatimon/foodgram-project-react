from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginators import LimitPagination
from .permissions import IsOwnerOrReadOnly
from recipes.models import (FavoritRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from .serializers import (CustomUserSerializer,
                          IngredientSerializer,
                          FavoriteSerializer,
                          RecipeReadSerializer,
                          RecipeCreateUpdateSerializer,
                          SubscribeListSerializer,
                          ShoppingCartSerializer,
                          TagSerializer)

from users.models import Subscription

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователя."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitPagination

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, args, kwargs)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],)
    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        serializer = SubscribeListSerializer(author,
                                             data=request.data,
                                             context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        Subscription.objects.create(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)

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

    @staticmethod
    def add_recipe(request, serializer, pk):
        """Статический метод для добавления рецептов в корзину и избранное."""
        serializer = serializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_recipe(request, model, **kwargs):
        """Статический метод для удаления рецептов из корзины и избранного."""
        recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
        if model.objects.filter(user=request.user,
                                recipe=recipe).exists():
            model.objects.filter(user=request.user,
                                 recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        return self.add_recipe(request, FavoriteSerializer, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, **kwargs):
        return self.delete_recipe(request, FavoritRecipe, **kwargs)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.add_recipe(request, ShoppingCartSerializer, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, **kwargs):
        return self.delete_recipe(request, ShoppingCart, **kwargs)

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
