from django.db.models import Sum
from rest_framework import response, status
from rest_framework.generics import get_object_or_404

from recipes.models import Recipe, RecipeIngredient


def ingredients_export(user):
    """Экспорт списка покупок в формате *.txt файла."""
    product_lst = RecipeIngredient.objects.filter(
        recipe__shopping_card__user=user).select_related('shopping_card',
                                                         'user').values_list(
        'ingredient__name', 'ingredient__measurement_unit').annotate(
        total_amount=Sum('amount'))
    product_list = [f'{name} {amount} {unit}\n'
                    for name, unit, amount in product_lst]
    return ''.join(product_list)


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
