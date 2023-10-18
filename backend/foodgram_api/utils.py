from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


def create_instans(request, id, serializer_name, model):
    recipe = model.objects.filter(id=id).exists()
    if not recipe:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    serializer = serializer_name(
        data={
            'user': request.user.id,
            'recipe': get_object_or_404(model, id=id).id
        },
        context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_instans(request, id, model, related_model):
    if not related_model.objects.filter(
        user=request.user, recipe=get_object_or_404(model, pk=id)
    ).exists():
        return Response(status=status.HTTP_400_BAD_REQUEST)
    related_model.objects.get(user=request.user.id, recipe=id).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def ingredient_valid(serializers, data, ingredient_model):
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
        if not ingredient_model.objects.filter(
            id=ingredient.get('id')
        ).exists():
            raise serializers.ValidationError(
                'Выбран несуществующий ингредиент!'
            )
        ingredients_list.append(ingredient.get('id'))
    if len(set(ingredients_list)) != len(ingredients_list):
        raise serializers.ValidationError(
            'Ингредиенты не могут повторяться!'
        )


def tag_valid(serializers, data, ingredient_model):
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
        if not ingredient_model.objects.filter(id=tag.id).exists():
            raise serializers.ValidationError(
                'Выбран несуществующий тег!'
            )
        tags_list.append(tag)
