from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db.transaction import atomic
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, relations, serializers, status

from recipes.models import (
    FavoriteRecipeUser,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCartUser,
    Tag,
)
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэга."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента"""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class CustomUserSerializer(UserSerializer):
    """
    Определение логики сериализации объектов кастомной модели
    пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'username',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and obj.following.filter(user=user).exists())


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name',
            'email', 'username', 'password')


class RecipeInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        if FavoriteRecipeUser.objects.filter(
                recipe=self.instance, user=user).exists():
            raise serializers.ValidationError(
                detail='Рецепт уже в избранных',
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


class FollowSerializer(serializers.ModelSerializer):
    """
       Определение логики сериализации для объектов модели
       подписок пользователя. Эндпоинт поддерживает ограничение
       количества отображаемых рецептов пользователя с помощью
       параметра эндпоинта 'recipes_limit'.
       """
    id = serializers.ReadOnlyField(source='author.id')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    username = serializers.ReadOnlyField(source='author.username')
    email = serializers.ReadOnlyField(source='author.email')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        model = Follow
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email',
            'is_subscribed',
            'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=self.context.get('request').user,
            author=obj.author
        ).exists()

    def get_recipes(self, attrs):
        author = attrs.author
        all_recipes = Recipe.objects.filter(author=author)
        return RecipeInfoSerializer(all_recipes, many=True).data

    def get_recipes_count(self, attrs):
        author = attrs.author
        all_recipes = Recipe.objects.filter(author=author)
        return all_recipes.count()

    def validate(self, attrs):
        author = self.context.get('author')
        user = self.context.get('request').user
        if author == user:
            raise serializers.ValidationError(
                {'error': 'Нельзя подписываться на самого себя'}, code=400)
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'error': 'Вы уже подписаны на данного автоора'}, code=400)
        return attrs


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для чтения (отображения) объектов модели
    ингредиентов в рецепте.
    """
    id = serializers.PrimaryKeyRelatedField(read_only=True,
                                            source='ingredient')
    name = serializers.SlugRelatedField(source='ingredient',
                                        slug_field="name",
                                        read_only=True)
    measurement_unit = serializers.SlugRelatedField(
        source="ingredient", slug_field="measurement_unit",
        read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для чтения (отображения) объектов модели
    рецептов.
    """
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientRecipeSerializer(
        read_only=True,
        many=True,
        source='ingredient_list'
    )
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.BooleanField(default=False,
                                            read_only=True)
    is_in_shopping_cart = serializers.BooleanField(default=False,
                                                   read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )


class IngredientAmountSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для записи объектов модели ингредиентов
    в рецепте.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipePostSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для записи объектов модели рецептов.
    - Запись изображение осуществляется в кодированном (base64) формате.
    - Список тегов и ингредиентов устанавливается через идентификаторы ('id')
    объектов этих моделей.
    """
    author = CustomUserSerializer(read_only=True)
    tags = relations.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ("author",)

    @staticmethod
    def validate_ingredients(ingredients):
        """Метод проверки уникальности и количества
         ингредиентов в рецепте."""
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо выбрать ингредиенты!'
            )
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество не может быть меньше 1!'
                )

        ids = [ingredient['id'] for ingredient in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Данный ингредиент уже есть в рецепте!'
            )
        return ingredients

    @staticmethod
    def validate_tags(self, data):
        """Метод проверки уникальности и наличия тегов в рецепте."""
        tags = self.initial_data.get("tags", False)
        if not tags:
            raise serializers.ValidationError(
                'Необходимо выбрать теги!'
            )
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise exceptions.ValidationError(
                    {"tags": "Нельзя использовать повторяющиеся теги!"}
                )
            tags_list.append(tag)
        return data

    @atomic
    def add_ingredients(self, ingredients, recipe):
        """Запись ингредиентов и их количества в рецепт."""
        for ingredient in ingredients:
            RecipeIngredient.objects.get_or_create(
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
                recipe=recipe, )

    @atomic
    def create(self, validated_data):
        """
        Переопределение метода записи рецепта с дополнительной проверкой
        на наличие уникальной записи
        """
        try:
            ingredients = validated_data.pop('ingredients')
            tags = validated_data.pop('tags')
            author = self.context.get('request').user
            recipe = Recipe.objects.create(author=author, **validated_data)
            recipe.save()
            recipe.tags.set(tags)
            self.add_ingredients(ingredients, recipe)
            return recipe
        except IntegrityError:
            error_message = (
                "Название рецепта с данным именем у Вас уже существует!"
            )
            raise serializers.ValidationError({"error": error_message})

    def update(self, instance, validated_data):
        """Переопределение метода обновления записи рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.tags.clear()
        instance.ingredients.clear()
        instance = super().update(instance, validated_data)
        self.add_ingredients(recipe=instance, ingredients=ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Переопределение перечня полей, возвращаемых эндпоинтом при успешном
        завершении операции добавления/обновления данных рецепта.
        """
        request = self.context.get("request")
        context = {"request": request}
        return RecipeSerializer(instance, context=context).data


class FavoritesAndShoppingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления рецептов в список избранного и корзину.
    """

    class Meta:
        message = None
        model = None
        abstract = True
        fields = ("user", "recipe")

    def validate(self, attrs):
        user = attrs["user"]
        recipe = attrs["recipe"]

        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError({"errors": [self.Meta.message]})

        return attrs

    def to_representation(self, instance):
        request = self.context.get("request")
        return RecipeShortRepresentationSerializer(
            instance.recipe, context={"request": request}
        ).data


class RecipeShortRepresentationSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для отображения сокращенного набора
    полей для объектов модели рецептов.
    """
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoritesWriteSerializer(FavoritesAndShoppingSerializer):
    """
    Определение логики сериализации для добавления рецептов в список
    избранного.
    """

    class Meta(FavoritesAndShoppingSerializer.Meta):
        model = FavoriteRecipeUser
        message = "Рецепт уже добавлен в список избранного!"


class ShoppingCartWriteSerializer(FavoritesAndShoppingSerializer):
    """
    Определение логики сериализации для добавления рецептов в корзину (список
    покупок).
    """

    class Meta(FavoritesAndShoppingSerializer.Meta):
        model = ShoppingCartUser
        message = "Рецепт уже добавлен в список покупок!"


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор установки пароля."""
    new_password = serializers.CharField(
        max_length=settings.DEFAULT_MAX_LENGTH,
        required=True)
    current_password = serializers.CharField(
        max_length=settings.DEFAULT_MAX_LENGTH,
        required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
