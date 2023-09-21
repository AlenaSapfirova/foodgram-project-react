# backend/api/tests.py
from http import HTTPStatus

from django.test import Client, TestCase


class foodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_recipes_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_ingredients_exists(self):
        """Проверка доступности списка ингредиентов."""
        response = self.guest_client.get('api/ingredients')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_tags_exists(self):
        """Проверка доступности списка тэгов."""
        response = self.guest_client.get('api/recipes/tags')
        self.assertEqual(response.status_code, HTTPStatus.OK)
    
    def test_list_users_exists(self):
        """Проверка доступности списка пользователей."""
        response = self.guest_client.get('api/users')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # def test_recipe_creation(self):
    #     """Проверка создания рецепта."""
    #     data = {
    #         'name': 'Test',
    #         'text': 'Test'
    #         'tags': '1',
    #         }
    #     response = self.guest_client.post('/api/tasks/', data=data)
    #     self.assertEqual(response.status_code, HTTPStatus.CREATED)
    #     self.assertTrue(models.Task.objects.filter(title='Test').exists())
