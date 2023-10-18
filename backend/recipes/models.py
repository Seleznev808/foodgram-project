from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

from .constants import (MAX_COOKING_TIME, MEASUREMENT_UNIT_MAX_LENGTH,
                        MINIMUM_AMOUNT_OF_INGREDIENTS, MINIMUM_COOKING_TIME,
                        NAME_MAX_LENGTH, SLUG_MAX_LENGTH)


class Ingredient(models.Model):
    name = models.CharField(
        'Ингредиент',
        max_length=NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        'Тег',
        max_length=NAME_MAX_LENGTH,
        unique=True
    )
    color = ColorField(
        default='#FF0000',
        image_field='Цвет',
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=SLUG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        'Название рецепта',
        max_length=NAME_MAX_LENGTH
    )
    image = models.ImageField(
        'Картинка рецепта',
        upload_to='recipes/',
    )
    text = models.TextField(
        'Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientsInRecipe',
        related_name='ingredients',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='tags',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(
                MINIMUM_COOKING_TIME,
                message='Время притовления не может быть меньше одной минуты!'
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message='Слишком большое время приготовления!'
            )
        )
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientsInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество ингредиентов',
        validators=(
            MinValueValidator(
                MINIMUM_AMOUNT_OF_INGREDIENTS,
                message='Количество ингредиентов не может быть меньше одного!'
            ),
        )
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.ingredient.name} для рецепта {self.recipe.name}'


class EnumRecipes(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s_recipe'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)s_recipe'
    )

    class Meta:
        abstract = True


class Favourites(EnumRecipes):

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='Вы не можете добавить в избранное свой рецепт!'
            ),
        )

    def __str__(self):
        return f'{self.recipe.name} - избранный рецепт {self.user.username}'


class ShoppingCart(EnumRecipes):

    class Meta:
        verbose_name = 'Рецепт с списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='Вы уже добавили этот рецепт в список покупок!'
            ),
        )

    def __str__(self):
        return f'{self.recipe.name} в списке покупок {self.user.username}'
