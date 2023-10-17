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
