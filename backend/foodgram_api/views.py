from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favourites, Ingredient, IngredientsInRecipe,
                            Recipe, ShoppingCart, Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (CastomUserSerializer, FavouritesSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeReadSerializer,
                          ShoppingCartSerializer, TagSerializer)
from .utils import create_instans, delete_instans


class CastomUserViewSet(UserViewSet):
    """Создание нового пользователя.

    Получение: списка пользователей,
    профиля пользователя, текущего пользователя.
    """

    queryset = User.objects.all()
    serializer_class = CastomUserSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_me(request):
    """Просмотр своего профиля."""
    user = get_object_or_404(User, username=request.user)
    serializer = CastomUserSerializer(
        user, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


class SubscriptionUserViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Работа с подписками.

    Получение списка пользователей, на которых подписан текущий пользователь,
    подписаться на пользователя, отписаться от пользователя.
    """

    serializer_class = FollowSerializer
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        """Возвращает queryset в зависимости от значения параметра limit."""
        queryset = User.objects.filter(following__user=self.request.user)
        limit = self.request.query_params.get('limit')
        if limit:
            queryset = queryset[:int(limit)]
        return queryset

    def create(self, request, id):
        """Создание новой подписки."""
        author = get_object_or_404(User, pk=id)
        serializer = FollowSerializer(
            author, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        Follow.objects.create(user=self.request.user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаление подписки."""
        if not Follow.objects.filter(
            user=request.user, author=get_object_or_404(User, id=id)
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.get(user=request.user.id, author=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение одного ингредиента или списка ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение одного тега или списка тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Работа с рецептами.

    Получение одного рецепта или списка рецептов,
    создание и обновление рецептов.
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        """Возвращает queryset в зависимости от метода."""
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeCreateSerializer


class FavouritesViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Добавление и удаление рецепта из избранного."""

    permission_classes = (IsAuthenticated,)

    def create(self, request, id):
        """Добавляет рецепт в избранное."""
        return create_instans(request, id, FavouritesSerializer, Recipe)

    def delete(self, request, id):
        """Удаляет рецепт из избранного."""
        return delete_instans(request, id, Recipe, Favourites)


class ShoppingCartViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Добавление и удаление рецепта из списка покупок."""

    permission_classes = (IsAuthenticated,)

    def create(self, request, id):
        """Добавляет рецепт в список покупок."""
        return create_instans(request, id, ShoppingCartSerializer, Recipe)

    def delete(self, request, id):
        """Удаляет рецепт из списка покупок."""
        return delete_instans(request, id, Recipe, ShoppingCart)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    """Скачивание списка покупок."""
    ingredients = IngredientsInRecipe.objects.filter(
        recipe__shoppingcart_recipe__user=request.user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(ingredient_amount=Sum('amount'))
    shopping_list = 'Список покупок:\n\n'
    shopping_list += '\n'.join([
        f'- {ingredient["ingredient__name"]}'
        f'({ingredient["ingredient__measurement_unit"]})'
        f' - {ingredient["ingredient_amount"]}'
        for ingredient in ingredients
    ])
    response = HttpResponse(shopping_list, content_type='text.txt')
    response['Content-Disposition'] = 'attachment; filename="shopping_cart"'
    return response
