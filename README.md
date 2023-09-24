# praktikum_new_diplomПроект "Продуктовый помошник" (Foodgram) предоставляет пользователям следующие возможности:
ПРОЕКТ ФУДГРАМ
регистрироваться
создавать свои рецепты и управлять ими (корректировать\удалять)
просматривать рецепты других пользователей
добавлять рецепты других пользователей в "Избранное" и в "Корзину"
подписываться на других пользователей
скачать список ингредиентов для рецептов, добавленных в "Корзину"

Установка :
 - установите Docker на свой компьютер. Вся информация об этом есть на официальном сайте (https://docs.docker.com/engine/install/)
  - склонируйте на свой проект репозиторий https://github.com/AlenaSapfirova/foodgram-project-react
  - установите окружение 
  - в крорневой папке проекта выполите команду docker-compose up -d --build
  - выполинте миграции docker-compose exec backend python manage.py migrate
  - соберите статику docker-compose exec backend python manage.py collectstatic --no-input
  - загрузите базу ингредиентов sudo docker exec -it foodgram-project-react-backend-1 bash -> python manage.py load_base
  

Корректировка\доработка репозитория:
В случае необходимости внесения каких-либо измениний в код проекта или в его функционал , после внесения измениений пересоберите образы и запуште их на DockerHub
В зависимости от того , в какой директории были данные изменения, выполните команды:
- docker build -t alenasap/foodgram_<backend/frontend/gateway> .
- docker push alenasap/foodgram_<backend/frontend/gateway>
Команды выполняются в той директории. в которою были внесены изменения.
Из корневой папки проекта последовательно выполните команды:
 - git -add .
 - git commit -m <ваш комментарий>
 - git push
 Проследите на странице за правильностью выполнения деплоя на каждом его этапе. В случае появления ошибки разверните тот этап, который закончился с ошибкой. Решения большинства ошибок можно най ти здесь https://stackoverflow.com/

 Алгоритм регистрации пользователей
Для добавления нового пользователя нужно отправить POST-запрос на эндпоинт:

POST /api/users/
В запросе необходимо передать поля:
email - (string) почта пользователя;
username - (string) уникальный юзернейм пользователя;
first_name - (string) имя пользователя;
last_name - (string) фамилия пользователя;
password - (string) пароль пользователя.
Пример запроса:

{
"email": "vpupkin@yandex.ru",
"username": "vasya.pupkin",
"first_name": "Вася",
"last_name": "Пупкин",
"password": "Qwerty123"
}
Далее необходимо получить авторизационный токен, отправив POST-запрос на эндпоинт:

POST /api/auth/token/login/
В запросе необходимо передать поля:
password - (string) пароль пользователя;
email - (string) почта пользователя.
Пример запроса:

{
"password": "Qwerty123",
"email": "vpupkin@yandex.ru"
}
Пример ответа:

{
  "auth_token": "string"
}
Поученный токен всегда необходимо передавать в заголовке (Authorization: Token TOKENVALUE) для всех запросов, которые требуют авторизации.

Изменение пароля текущего пользователя:
POST /api/users/set_password/
Пример запроса:

{
  "new_password": "string",
  "current_password": "string"
}
Удаление токена пользователя:
POST /api/auth/token/logout/
Регистрация пользователей админом
Пользователя может создать администратор через админ-зону сайта. Получение токена осуществляется способом, описанным выше.

Примеры использования API для неавторизованных пользователей:
Для неавторизованных пользователей работа с API доступна в режиме чтения.

GET /api/users/- получить список всех пользователей.
GET /api/tags/- получить список всех тегов.
GET /api/tags/{id}/ - получить тег по ID.
GET /api/recipes/- получить список всех рецептов.
GET /api/recipes/{id}/ - получить рецепт по ID.
GET /api/users/subscriptions/ - получить список всех пользователей, на которых подписан текущий пользователь. В выдачу добавляются рецепты.
GET /api/ingredients/ - получить список ингредиентов с возможностью поиска по имени.
GET /api/ingredients/{id}/ - получить ингредиент по ID.
Пример GET-запроса:
GET /api/recipes/
Пример ответа:
код ответа сервера: 200 OK
тело ответа:
{
  "count": 123,
  "next": "http://alenasap.ddns.net/api/recipes/?page=4",
  "previous": "http://alenasap.ddns.net/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "color": "#E26C2D",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Пупкин",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://alenasap.ddns.net/media/recipes/images/2023/09/09/23/23/temp.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}

Пример POST-запроса:
POST /api/recipes/

{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
Пример ответа:
код ответа сервера: 201
тело ответа:
{
"id": 0,
"tags": [
{}
],
"author": {
"email": "user@example.com",
"id": 0,
"username": "string",
"first_name": "Вася",
"last_name": "Пупкин",
"is_subscribed": false
},
"ingredients": [
{
"id": 0,
"name": "Картофель отварной",
"measurement_unit": "г",
"amount": 1
}
],
"is_favorited": true,
"is_in_shopping_cart": true,
"name": "string",
"image": "http://alenasap.ddns.net/media/recipes/images/2023/09/09/23/23/temp.jpeg",
"text": "string",
"cooking_time": 1
} 

После запуска проект будкт досступен по доменном имени alenasap.ddns.net