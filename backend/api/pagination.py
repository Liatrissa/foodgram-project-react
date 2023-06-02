from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Пагинация для списка рецептов"""
    page_size = settings.PAGE_SIZE
    page_size_query_param = 'limit'
