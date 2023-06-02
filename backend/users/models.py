from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя"""

    username = models.CharField(
        verbose_name='Логин',
        max_length=settings.DEFAULT_MAX_LENGTH,
        unique=True,
        blank=False,
        help_text='Введите логин',
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+',
                message='Используйте допустимые символы в username'),
        ],
        error_messages={
            'unique': 'Пользователь с таким логином уже существует',
        },
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=settings.DEFAULT_MAX_LENGTH,
        help_text='Введите имя')
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=settings.DEFAULT_MAX_LENGTH,
        help_text='Введите фамилию',)
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=settings.EMAIL_MAX_LENGTH,
        unique=True,
        help_text='Введите e-mail',)
    password = models.CharField(
        verbose_name='Пароль',
        max_length=settings.DEFAULT_MAX_LENGTH,
        blank=False,
        help_text='Введите пароль')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
        'password',
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-id']

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписок на других пользователей"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписавшийся",
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = 'Подписка на автора'
        verbose_name_plural = 'Подписки на авторов'
        ordering = ("-id",)
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(following=models.F("user")),
                name="no_self_follow"),
        ]

    def __str__(self):
        return (
            f'Пользователь {self.user} подписан на '
            f' {self.following}'
        )
