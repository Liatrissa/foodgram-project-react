from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import relations, serializers

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
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """
       Определение логики сериализации для объектов модели
       подписок пользователя.
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
                {'error': 'Вы уже подписаны на данного автора'}, code=400)
        return attrs


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для чтения (отображения) объектов модели
    ингредиентов в рецепте.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

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
    author = CustomUserSerializer(many=False, read_only=True)
    ingredients = IngredientRecipeSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredients'
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_card.filter(recipe=recipe).exists()


class IngredientAmountSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для записи объектов модели ингредиентов
    в рецепте.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

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
    tags = relations.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "image",
            "tags",
            "author",
            "ingredients",
            "name",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    @transaction.atomic
    def create(self, validated_data):
        """
        Переопределение метода записи рецепта
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount'))
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Переопределение метода обновления записи рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.add(*tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for field, value in validated_data.items():
            setattr(instance, field, value)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient.get('id'),
                recipe=instance,
                amount=ingredient.get('amount'))
        instance.save()
        return instance

    def validate(self, attrs):
        ingredients = attrs.get('ingredients', [])
        ingredients_id = []
        if not attrs.get('cooking_time') > 0:
            raise serializers.ValidationError(
                {"cooking_time": "cooking_time должно быть больше 0"})
        for elem in ingredients:
            current_id = elem.get('id')
            amount = elem.get('amount')
            if current_id not in ingredients_id:
                ingredients_id.append(current_id)
            if not amount > 0:
                raise serializers.ValidationError(
                    {"amount": "значение количества должно быть > 0"})
        return attrs

    def to_representation(self, instance):
        """
        Переопределение перечня полей, возвращаемых эндпоинтом при успешном
        завершении операции добавления/обновления данных рецепта.
        """
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class FavoritesWriteSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для добавления рецептов в список
    избранного.
    """

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = FavoriteRecipeUser
        fields = ('id', 'name', 'cooking_time', 'image')

    def validate(self, attrs):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        if FavoriteRecipeUser.objects.filter(user=user,
                                             recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'рецепт уже в избранном'}, code=400)
        return attrs


class ShoppingCartWriteSerializer(serializers.ModelSerializer):
    """
    Определение логики сериализации для добавления рецептов в корзину (список
    покупок).
    """

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCartUser
        fields = ('id', 'name', 'cooking_time', 'image')

    def validate(self, attrs):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        if ShoppingCartUser.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'рецепт уже в списке покупок'}, code=400)
        return attrs


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
