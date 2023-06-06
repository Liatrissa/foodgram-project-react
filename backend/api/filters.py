from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe
from users.models import User


class IngredientFilter(FilterSet):
    """Фильтр для поиска по названию ингредиента"""
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    """
    Набор фильтров, которые можно применить к запросам, чтобы фильтровать
    объекты модели Recipe
    """
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug', )
    author = filters.ModelChoiceFilter(
        queryset=User.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_shopping_cart'
    )

    def filter_favorited(self, queryset, name, value):
        """
        Фильтр возвращает объекты рецептов, которые находятся в избранном
        для данного пользователя.
        """
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        """
        Фильтр возвращает объекты рецептов, которые находятся в корзине
        для данного пользователя.
        """
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
