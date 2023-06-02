from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        unique=True,
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Тег',
        help_text='Введите название тега', )
    color = models.CharField(
        unique=True,
        max_length=settings.HEX_CODE_MAX_LENGTH,
        verbose_name='Цветовой HEX-код',
        help_text='Введите Цветовой HEX-код (например: #00b8ff)', )

    slug = models.SlugField(
        unique=True,
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Слаг тега',
        help_text='Введите слаг тега', )

    class Meta:
        ordering = ("id",)
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self) -> str:
        return (f'{self.name}'
                f'(цвет: {self.color})')


class Ingredient(models.Model):
    """Модель избранного ингредиента"""
    name = models.CharField(
        db_index=True,
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Название',
        help_text='Введите название ингредиента', )
    measurement_unit = models.CharField(
        default='г',
        max_length=settings.CONTENT_MAX_LENGTH,
        verbose_name='Единицы измерения',
        help_text='Введите единицы измерения', )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    """Модель рецепта"""
    name = models.CharField(
        max_length=settings.HEX_CODE_MAX_LENGTH,
        verbose_name='Название блюда',
        db_index=True,
        help_text='Введите название блюда',
    )
    text = models.TextField(help_text='Введите текст рецепта',
                            verbose_name='Описание блюда')
    cooking_time = models.IntegerField(
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

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ("-id",)

    def __str__(self):
        return f'{self.name}'


class RecipeIngredient(models.Model):
    """Модель для связи рецепта и соответствующих ему ингредиентов."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиента в рецепте',
        help_text="Введите количество ингредиентов",
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления не может быть меньше 1 минуты', )
        ],
    )

    class Meta:
        verbose_name = 'Связь ингредиента c рецептом'
        verbose_name_plural = 'Связи ингредиентов c рецептами'
        constraints = [
            models.UniqueConstraint(
                name='unique_ingredient_recipe',
                fields=['ingredient', 'recipe'],
            ),
        ]

    def __str__(self):
        return f'Ингредиент {self.ingredient} в рецепте {self.recipe}'


class ShoppingCartUser(models.Model):
    """Модель корзины покупок (отношение рецепт-пользователь)"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_in_shoplist',
        verbose_name='Пользователь, имеющий рецепт в cписке покупок',
        help_text='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_in_shoplist',
        verbose_name='Рецепт из списка покупок пользователя',
        help_text='Рецепт в списке покупок', )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                name='unique_user_shoplist',
                fields=['user', 'recipe'],
            ),
        ]

    def __str__(self):
        return f'У {self.user} в списке покупок рецепт: {self.recipe}'


class FavoriteRecipeUser(models.Model):
    """Модель избранных рецептов"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Пользователь, имеющий избранные рецепты',
        help_text='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Избранный рецепт определенного пользователя',
        help_text='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Список избранного'
        verbose_name_plural = 'Списки избранного'
        constraints = [
            models.UniqueConstraint(
                name='unique_favorite_recipe_user',
                fields=['user', 'recipe'],
            ),
        ]

    def __str__(self):
        return f'У {self.user} в избранном рецепт: {self.recipe}'
