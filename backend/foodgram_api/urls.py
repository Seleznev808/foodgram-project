from django.urls import include, path
from rest_framework import routers

from .views import (CastomUserViewSet, FavouritesViewSet, IngredientViewSet,
                    RecipeViewSet, ShoppingCartViewSet,
                    SubscriptionUserViewSet, TagViewSet,
                    download_shopping_cart, users_me)

router_v1 = routers.DefaultRouter()
router_v1.register(
    r'users/subscriptions',
    SubscriptionUserViewSet,
    basename='subscriptions'
)
router_v1.register(
    r'users/(?P<id>\d+)/subscribe',
    SubscriptionUserViewSet,
    basename='subscribe'
)
router_v1.register('users', CastomUserViewSet, basename='users')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
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
router_v1.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('users/me/', users_me),
    path('recipes/download_shopping_cart/', download_shopping_cart),
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
