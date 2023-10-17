import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favourites, Ingredient, IngredientsInRecipe,
                            Recipe, ShoppingCart, Tag)
from rest_framework import serializers, validators
from users.models import Follow, User


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


class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password'
        )


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


class Base64ImageField(serializers.ImageField):
    """Сериализатор для сохранения картинок."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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
        if not data.get('recipe'):
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        ingredients_list = []
        for ingredient in data.get('recipe'):
            if ingredient.get('amount') < 1:
                raise serializers.ValidationError(
                    'Количество ингредиентов не может быть меньше 1!'
                )
            if not Ingredient.objects.filter(id=ingredient.get('id')).exists():
                raise serializers.ValidationError(
                    'Выбран несуществующий ингредиент!'
                )
            ingredients_list.append(ingredient.get('id'))
        if len(set(ingredients_list)) != len(ingredients_list):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться!'
            )
        if not data.get('tags'):
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег!'
            )
        tags_list = []
        for tag in data.get('tags'):
            if tag in tags_list:
                raise serializers.ValidationError(
                    'Теги не могут повторяться!'
                )
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Выбран несуществующий тег!'
                )
            tags_list.append(tag)
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
