from django.db.models import Sum

from recipes.models import RecipeIngredient


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
