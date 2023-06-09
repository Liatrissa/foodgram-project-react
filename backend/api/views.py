from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Value
from django.db.models.fields import BooleanField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    FavoriteRecipeUser,
    Ingredient,
    Recipe,
    ShoppingCartUser,
    Tag,
)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import AuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    FavoritesWriteSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipePostSerializer,
    RecipeSerializer,
    SetPasswordSerializer,
    ShoppingCartWriteSerializer,
    TagSerializer,
)
from .utils import add_delete, ingredients_export


class PermissionMixin:
    """Миксина для списка тегов и ингредиентов."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class TagsViewSet(PermissionMixin, viewsets.ModelViewSet):
    """Вьюсет для работы с тэгами"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(PermissionMixin, viewsets.ModelViewSet):
    """Вьюсет для работы с ингредиентами"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class CustomUserViewSet(UserViewSet):
    """
    Набор представлений для работы с пользователями.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    http_method_names = ['get', 'post', 'delete']

    @action(
        detail=False, methods=(['get']),
        permission_classes=[IsAuthenticated]
    )
    def get_user_me(self, request):
        """Метод обрабатывающий эндпоинт me."""
        serializer = CustomUserSerializer(request.user,
                                          context={'request': request})
        return Response(serializer.data)

    @action(detail=False,
            permission_classes=(IsAuthenticated,),
            methods=['post', 'get'])
    def set_password(self, request):
        """Метод обрабатывающий эндпоинт set_password."""
        user = get_object_or_404(User, email=request.user.email)
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if check_password(request.data['current_password'], user.password):
            new_password = make_password(request.data['new_password'])
            user.password = new_password
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {
                'current_password':
                    'Введенный и текущий пароли не совпадают'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """
        Метод обрабатывающий эндпоинт subscriptions.
        Возвращает пользователей, на которых подписан текущий пользователь.
        В выдачу добавляются рецепты.
        """
        user = request.user
        subscriptions = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        """
        Эндпоинт для добавления / удаления подписки на пользователя.
        Доступно только авторизованным пользователям.
        """
        if self.request.method == 'POST':
            user = get_object_or_404(User, pk=kwargs.get('id'))
            context = {'request': self.request, 'user': user}
            serializer = FollowSerializer(data=request.data,
                                          context=context)
            if serializer.is_valid(raise_exception=True):
                serializer.save(user=request.user, author=user)
                return Response(data=serializer.data,
                                status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            user = request.user
            author = get_object_or_404(User, pk=kwargs.get('id'))
            if not Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'error': 'Вы не были подписаны на данного пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)
            follow = get_object_or_404(Follow, user=user, author=author)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами. В представлении используются
    два отдельных серилизатора для чтения и записи объектов модели.
    """
    permission_classes = (AuthorOrReadOnly, )
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recipe.objects.add_user_annotations(self.request.user.id)
        return Recipe.objects.add_user_annotations(
            Value(None, output_field=BooleanField()))

    def get_serializer_class(self):
        """
        Изменение типа вызываемого сериализатора, в зависимости от метода
        запроса.
        """
        if self.action in ['create', 'partial_update']:
            return RecipePostSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True,
            permission_classes=(IsAuthenticated,),
            methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Эндпоинт для избранных рецептов."""
        return add_delete(FavoritesWriteSerializer,
                          FavoriteRecipeUser,
                          request,
                          pk)

    @action(detail=True,
            permission_classes=(IsAuthenticated,),
            methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        """Эндпоинт для добавления/ удаления рецепта для списка покупок."""
        return add_delete(ShoppingCartWriteSerializer,
                          ShoppingCartUser,
                          request,
                          pk)

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            methods=['get'])
    def download_shopping_cart(self, request):
        """Эндпоинт для загрузки списка покупок."""
        product_list = ingredients_export(request.user)
        response = HttpResponse(product_list,
                                content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename={settings.SHOPPING_CART}')
        return response
