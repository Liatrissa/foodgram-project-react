from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef

from users.models import User


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        unique=True,
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Тег',
        help_text='Введите название тега', )
    color = models.CharField(
        max_length=settings.HEX_CODE_MAX_LENGTH,
        verbose_name='Цветовой HEX-код',
        help_text='Введите Цветовой HEX-код (например: #00b8ff)', )

    slug = models.SlugField(
        unique=True,
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Слаг тега',
        help_text='Введите слаг тега', )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'color'], name='unique_name_color'
            )
        ]

    def __str__(self) -> str:
        return (f'Тэг: {self.name}'
                f'цвет: {self.color}'
                f'Slug: {self.slug}')


class Ingredient(models.Model):
    """Модель избранного ингредиента"""
    name = models.CharField(
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Название',
        help_text='Введите название ингредиента', )
    measurement_unit = models.CharField(
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Единицы измерения',
        help_text='Введите единицы измерения', )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return (f'Ингредиент: {self.name}',
                f' Единица измерения:{self.measurement_unit}.')


class RecipeQuerySet(models.QuerySet):
    """
    Добавление поля is_favorited для определения добавления рецепта
    в избранное.
    Добавление поля is_in_shopping_cart для определения добавления рецепта
    в список покупок.
    """
    def filter_by_tags(self, tags):
        if tags:
            return self.filter(tags__slug__in=tags).distinct()
        return self

    def add_user_annotations(self, user_id):
        return self.annotate(
            is_favorited=Exists(
                FavoriteRecipeUser.objects.filter(
                    user_id=user_id, recipe__pk=OuterRef('pk')
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCartUser.objects.filter(
                    user_id=user_id, recipe__pk=OuterRef('pk'))
            ),
            in_shopping_cart=Exists(
                ShoppingCartUser.objects.filter(
                    user_id=user_id, recipe__pk=OuterRef('pk'))
            )
        )


class Recipe(models.Model):
    """Модель рецепта"""
    name = models.CharField(
        max_length=settings.HEX_CODE_MAX_LENGTH,
        verbose_name='Название блюда',
        help_text='Введите название блюда',
    )
    text = models.TextField(help_text='Введите текст рецепта',
                            verbose_name='Описание блюда')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        help_text='Введите время приготовления в минутах',
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления не может быть меньше 1 минуты', )
        ]
    )
    image = models.ImageField(verbose_name='Изображение блюда',
                              help_text='Добавьте картинку блюда',
                              upload_to='recipes/images/')
    author = models.ForeignKey(User,
                               verbose_name='Автор рецепта',
                               related_name='recipes',
                               help_text="Введите автора рецепта",
                               on_delete=models.CASCADE, )
    tags = models.ManyToManyField(Tag, related_name="tags")
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='ingredients_recipes',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта',
        help_text="Введите дату публикации поста",
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'], name='unique_name_author_recip'
            )
        ]

    def __str__(self):
        return (f'Рецепт: {self.name}, Описание: {self.text[:100]},'
                f'Время приготовления: {self.cooking_time} мин.')


class RecipeIngredient(models.Model):
    """Модель для связи рецепта и соответствующих ему ингредиентов."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиента в рецепте',
        help_text="Введите количество ингредиентов",
        validators=[
            MinValueValidator(
                1,
                message='Количество не может быть меньше 1', )
        ],
    )

    class Meta:
        verbose_name = 'Связь ингредиента c рецептом'
        verbose_name_plural = 'Связи ингредиентов c рецептами'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_recipe'
            )
        ]

    def __str__(self):
        return f'Ингредиент {self.ingredient} в рецепте {self.recipe}'


class TagRecipe(models.Model):
    """Модель для связи рецепта и соответствующего ему тега."""
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tag_recipes',
        verbose_name='тег',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tag_recipes',
        verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'Тег и рецепт'
        verbose_name_plural = 'Тег и рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'], name='unique_tag_recipe'
            )
        ]


class ShoppingCartUser(models.Model):
    """Модель корзины покупок (отношение рецепт-пользователь)"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_card',
        verbose_name='Пользователь, имеющий рецепт в cписке покупок',
        help_text='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_card',
        verbose_name='Рецепт из списка покупок пользователя',
        help_text='Рецепт в списке покупок', )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'У {self.user} в списке покупок рецепт: {self.recipe}'


class FavoriteRecipeUser(models.Model):
    """Модель избранных рецептов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь, имеющий избранные рецепты',
        help_text='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранный рецепт определенного пользователя',
        help_text='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Список избранного'
        verbose_name_plural = 'Списки избранного'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'У {self.user} в избранном рецепт: {self.recipe}'
