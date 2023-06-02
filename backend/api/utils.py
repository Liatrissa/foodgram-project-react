from datetime import date

from django.http import HttpResponse
from rest_framework import response, status
from rest_framework.generics import get_object_or_404

from recipes.models import Recipe


def ingredients_export(self, request, ingredients):
    """Экспорт списка покупок в формате *.txt файла."""
    user = self.request.user
    filename = f"{user.username}_shopping_list.txt"

    today = date.today()
    shopping_list = f"Список покупок пользователя: {user.username}\n\n"
    shopping_list += f"Дата: {today:%Y-%m-%d}\n\n"

    ingredient_lines = [
        f'- {ingredient["ingredient__name"]} '
        f'({ingredient["ingredient__measurement_unit"]}) - '
        f'{ingredient["amount"]}'
        for ingredient in ingredients
    ]
    shopping_list += "\n".join(ingredient_lines)
    shopping_list += f"\n\nFoodgram ({today:%Y})"

    response = HttpResponse(
        shopping_list, content_type="text/plain; charset=utf-8"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def add_delete(serializer_name, model, request, recipe_id):
    """
    Добавление / удаление рецепта в список избранного или корзину (список
    покупок) пользователя.
    """
    user = request.user
    data = {"user": user.id, "recipe": recipe_id}
    serializer = serializer_name(data=data, context={"request": request})
    if request.method == "POST":
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(
            serializer.data, status=status.HTTP_201_CREATED
        )
    get_object_or_404(
        model, user=user, recipe=get_object_or_404(Recipe, id=recipe_id)
    ).delete()
    return response.Response(status=status.HTTP_204_NO_CONTENT)
