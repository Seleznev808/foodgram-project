from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilter
from .permissions import IsAuthorOrAdminOrReadOnly, IsAuthorOrAdmin
from .serializers import (
    CastomUserSerializer,
    IngredientSerializer,
    FavouritesSerializer,
    FollowSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    TagSerializer
)
from recipes.models import (
    Favourites,
    Ingredient,
    IngredientsInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Follow, User


class CastomUserViewSet(UserViewSet):
    """Создание нового пользователя;
    получение:
        списка пользователей,
        профиля пользователя,
        текущего пользователя.
    """

    queryset = User.objects.all()
    serializer_class = CastomUserSerializer
    # @action(
    #     methods=('GET',),
    #     detail=False,
    #     url_path='me',
    #     permission_classes=(IsAuthenticated,)
    # )
    # def me(self, request):
    #     user = request.user
    #     serializer = CastomUserSerializer(user)
    #     return Response(serializer.data, status=status.HTTP_200_OK)


class SubscriptionUserViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Работа с подписками:
        получение списка пользователей, на которых подписан текущий пользователь,
        подписаться на пользователя,
        отписаться от пользователя.
    """

    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
    
    def get_user_and_author(self, request, id):
        user = self.request.user
        author = get_object_or_404(User, pk=id)
        return user, author

    def create(self, request, id):
        user, author = self.get_user_and_author(request, id)
        serializer = FollowSerializer(
            author, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        Follow.objects.create(user=user, author=author)
        # serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user, author = self.get_user_and_author(request, id)
        # subscription = Follow.objects.filter(user=user, author=author)
        # if not subscription:
        #     return Response(status=status.HTTP_400_BAD_REQUEST)
        # self.perform_destroy(subscription)
        subscription = get_object_or_404(
            Follow, user=user, author=author
        )
        if not subscription:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение одного ингредиента или списка ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение одного тега или списка тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Работа с рецептами:
        получение одного рецепта или списка рецептов,
        создание и обновление рецептов.
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeCreateSerializer


class FavouritesViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Добавление и удаление рецепта из избранного."""

    permission_classes = (IsAuthorOrAdmin,)
    # permission_classes = (IsAuthenticated,)

    def create(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        serializer = FavouritesSerializer(
            data={'user': request.user.id, 'recipe': recipe.id, },
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        if not Favourites.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        Favourites.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Добавление и удаление рецепта из списка покупок."""

    permission_classes = (IsAuthorOrAdmin,)
    # permission_classes = (IsAuthenticated,)

    def create(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id, },
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, pk=id)
        if not ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientsInRecipe.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = f'Список покупок:\n\n'
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        response = HttpResponse(shopping_list, content_type='application/txt')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart"'
        return response
