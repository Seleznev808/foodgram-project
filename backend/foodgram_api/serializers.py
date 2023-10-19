from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers, status, validators

from recipes.models import (Favourites, Ingredient, IngredientsInRecipe,
                            Recipe, ShoppingCart, Tag)
from users.models import Follow, User

from .utils import Base64ImageField, ingredient_valid, tag_valid


class CastomUserSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователях."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class RecipesForSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов для модели подписок."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(CastomUserSerializer):
    """Сериализатор для работы с подписками."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CastomUserSerializer.Meta):
        model = User
        fields = CastomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'request').query_params.get('recipes_limit')
        if recipes_limit:
            queryset = Recipe.objects.filter(
                author=obj.id)[:int(recipes_limit)]
        else:
            queryset = Recipe.objects.filter(author=obj.id).all()
        serializer = RecipesForSubscriptionsSerializer(
            instance=queryset, many=True
        )
        return serializer.data

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя!'
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для добавления в рецепт."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для получения рецепта."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецепта или списка рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = CastomUserSerializer(read_only=True)
    ingredients = IngredientGetSerializer(
        many=True, source='recipe'
    )
    image = Base64ImageField(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favourites.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания или изменения рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientsInRecipeSerializer(
        many=True, source='recipe'
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )

    def validate(self, data):
        ingredient_valid(serializers, data, Ingredient)
        tag_valid(serializers, data, Tag)
        if int(data.get('cooking_time')) < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше одной минуты!'
            )
        return data

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient, id=ingredient.get('id')
            )
            amount = ingredient.get('amount')
            ingredient_list.append(
                IngredientsInRecipe(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=amount
                )
            )
        IngredientsInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        user = self.context.get('request').user
        if user.is_anonymous:
            result = serializers.ValidationError(
                {'message': 'Вы не можете создать рецепт!'}
            )
            result.status_code = status.HTTP_401_UNAUTHORIZED
            raise result
        ingredients = validated_data.pop('recipe')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeReadSerializer(
            instance,
            context={'request': request}
        ).data


class FavouritesSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления или удаления избранных рецептов."""

    class Meta:
        model = Favourites
        fields = ('user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favourites.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в избранное!'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipesForSubscriptionsSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления или удаления в списке покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в список покупок!'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipesForSubscriptionsSerializer(
            instance.recipe,
            context={'request': request}
        ).data
