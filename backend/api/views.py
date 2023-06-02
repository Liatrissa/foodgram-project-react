from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Exists, OuterRef, Sum, Value
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    FavoriteRecipeUser,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCartUser,
    Tag,
)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipePagination
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
    filter_backends = (DjangoFilterBackend, SearchFilter,)
    filterset_class = IngredientFilter


class UserViewSet(viewsets.ModelViewSet):
    """
    Набор представлений для работы с пользователями.
    """
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    search_fields = ('username', 'email')
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return User.objects.all()

    @action(
        detail=False, methods=('get', 'patch', 'post',),
        url_path='me', url_name='me',
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_user_me(self, request):
        """Метод обрабатывающий эндпоинт me."""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """
        Метод обрабатывающий эндпоинт subscriptions.
        Возвращает пользователей, на которых подписан текущий пользователь.
        В выдачу добавляются рецепты.
        """
        user = request.user
        queryset = User.objects.filter(following__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk):
        """
        Эндпоинт для добавления / удаления подписки на пользователя.
        Доступно только авторизованным пользователям.
        """
        following = get_object_or_404(User, id=pk)
        user = request.user
        if request.method == 'POST':
            serializer = FollowSerializer(
                following,
                data=request.data,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, following=following)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(Follow, user=user, following=following).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами. В представлении используются
    два отдельных серилизатора для чтения и записи объектов модели.
    """
    permission_classes = (AuthorOrReadOnly,)
    pagination_class = RecipePagination
    filterset_class = RecipeFilter

    def get_queryset(self):
        """
        Добавление поля is_favorited для определения добавления рецепта
        в избранное.
        Добавление поля is_in_shopping_cart для определения добавления рецепта
        в список покупок.
        """
        return Recipe.objects.annotate(
            is_favorited=Exists(
                self.request.user.favorites.filter(recipe=OuterRef("pk"))
            )
            if self.request.user.is_authenticated
            else Value(False),
            is_in_shopping_cart=Exists(
                self.request.user.shopping_list.filter(recipe=OuterRef("pk"))
            )
            if self.request.user.is_authenticated
            else Value(False),
        )

    def get_serializer_class(self):
        """
        Изменение типа вызываемого сериализатора, в зависимости от метода
        запроса.
        """
        if self.request.method in ("POST", "PUT", "PATCH"):
            return RecipeSerializer
        return RecipePostSerializer

    def get_permissions(self):
        """
        Дополнительные условия на определение прав доступа для изначального
        создания объекта модели и изменение уже созданных объектов.
        """
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return super().get_permissions()

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
            permission_classes=(IsAuthenticated,),
            methods=['get'])
    def download_shopping_cart(self, request):
        """Эндпоинт для загрузки списка покупок."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_list__user=self.request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .order_by("ingredient__name")
            .annotate(amount=Sum("amount"))
        )
        return ingredients_export(self, request, ingredients)
