from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, F

from foodgram import constants


class User(AbstractUser):
    """Модель пользователя."""
    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True)
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=constants.MAX_LENGTH)
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=constants.MAX_LENGTH)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор рецепта')

    class Meta:
        ordering = ('id',)
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscriber'),
            models.CheckConstraint(
                check=Q(user=F('author')),
                name='no_subscribe_yourself')]

    def __str__(self):
        return f'Пользователь {self.user} подписан на {self.author}'
