from django_filters import CharFilter
from django_filters.rest_framework import BooleanFilter, FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


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
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all())
    author = CharFilter(field_name='author')
    is_favorited = BooleanFilter()
    is_in_shopping_cart = BooleanFilter()

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
