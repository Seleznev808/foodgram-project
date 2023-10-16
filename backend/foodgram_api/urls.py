from django.urls import include, path
from rest_framework import routers

from .views import (
    CastomUserViewSet,
    FavouritesViewSet,
    IngredientViewSet,
    SubscriptionUserViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    TagViewSet,
)


router_v1 = routers.DefaultRouter()
router_v1.register('users', CastomUserViewSet, basename='users')
router_v1.register(
    r'users/subscriptions',
    SubscriptionUserViewSet,
    basename='subscriptions')
router_v1.register(
    r'users/(?P<id>\d+)/subscribe',
    SubscriptionUserViewSet,
    basename='subscribe')
# router_v1.register(
#     r'users/me',
#     SubscriptionUserViewSet,
#     basename='me')

router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register(
    r'recipes/(?P<id>\d+)/favorite',
    FavouritesViewSet,
    basename='recipes-favorite'
)
router_v1.register(
    r'recipes/(?P<id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='recipes-shopping-cart'
)
router_v1.register(
    r'recipes/download_shopping_cart',
    ShoppingCartViewSet,
    basename='download-shopping-cart'
)

urlpatterns = [
    # path(
    #     'users/<int:id>/subscribe/',
    #     SubscriptionUserViewSet.as_view({'post': 'create'}),
    #     name='subscribe'
    # ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
