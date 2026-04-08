from django.contrib.auth import get_user_model
from django.test import TestCase


class TokenPairAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
        )

    def test_token_pair_success(self):
        response = self.client.post(
            '/api/token/pair',
            data={
                'email': self.user.email,
                'password': 'StrongPass123!',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('access', payload)
        self.assertIn('refresh', payload)

    def test_token_pair_invalid_password_returns_401(self):
        response = self.client.post(
            '/api/token/pair',
            data={
                'email': self.user.email,
                'password': 'WrongPass123!',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
