# Сайт "Продуктовый помощник"
Проект Foodgram продуктовый помощник - платформа для публикации рецептов.

![workflow](https://github.com/liatrissa/foodgram-project-react/actions/workflows/main.yml/badge.svg)

## Адрес развернутого приложения:

```
- Документация API: http://51.250.29.203/api/schema/redoc
- Панель администратора: http://51.250.29.203/admin/
- Главная страница сайта: http://51.250.29.203/recipes
```
## Ссылка на репозиторий:

```
https://github.com/Liatrissa/foodgram-project-react.git
```


## Описание проекта:
Проект Foodgram продуктовый помощник - платформа для публикации рецептов.
Cайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

 * Реализован бекенд.
 * Фронтенд - одностраничное приложение на фреймворке React, которое взаимодействует с API через удобный пользовательский интерфейс (разработан Яндекс.Практикум).


#### Структура репозитория
 * В папке frontend находятся файлы, необходимые для сборки фронтенда приложения.
 * В папке infra — заготовка инфраструктуры проекта: конфигурационный файл nginx и docker-compose.yml.
 * В папке backend бэкенд продуктового помощника.
 * В папке data подготовлен список ингредиентов с единицами измерения. Список сохранён в форматах JSON и CSV.
 * В папке docs — файлы спецификации API.

#### Инфраструктура (будет реализовано на втором этапе)
 * Проект работает с СУБД PostgreSQL.
 * Проект запущен на сервере в трёх контейнерах: nginx, PostgreSQL и Django+Gunicorn. Контейнер с проектом обновляется на Docker Hub.
 * В nginx настроена раздача статики, остальные запросы переадресуются в Gunicorn.
 * Данные сохраняются в volumes.

#### Базовые модели проекта

**Рецепт**

 * Автор публикации (пользователь).
 * Название.
 * Картинка.
 * Текстовое описание.
 * Ингредиенты: продукты для приготовления блюда по рецепту. Множественное поле, выбор из предустановленного списка, с указанием количества и единицы измерения.
 * Тег (можно установить несколько тегов на один рецепт, выбор из предустановленных).
 * Время приготовления в минутах.
 
**Тег**

 * Название.
 * Цветовой HEX-код (например, #49B64E).
 * Slug.

**Ингредиент**

 * Название.
 * Количество.
 * Единицы измерения.


### Автор
Алексеева Анастасия
