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


class AdminCreateUserAPITests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='StrongPass123!',
        )
        self.regular_user = get_user_model().objects.create_user(
            email='member@example.com',
            password='StrongPass123!',
        )

    def _get_access_token(self, email: str, password: str) -> str:
        response = self.client.post(
            '/api/token/pair',
            data={'email': email, 'password': password},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        return response.json()['access']

    def test_superuser_can_create_user(self):
        token = self._get_access_token('admin@example.com', 'StrongPass123!')

        response = self.client.post(
            '/api/admin/users',
            data={
                'email': 'new.user@example.com',
                'password': 'AnotherStrongPass123!',
                'first_name': 'New',
                'last_name': 'User',
                'is_staff': False,
                'is_active': True,
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(email='new.user@example.com').exists())

    def test_non_superuser_gets_403(self):
        token = self._get_access_token('member@example.com', 'StrongPass123!')

        response = self.client.post(
            '/api/admin/users',
            data={
                'email': 'blocked@example.com',
                'password': 'AnotherStrongPass123!',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 403)

    def test_duplicate_email_returns_409(self):
        token = self._get_access_token('admin@example.com', 'StrongPass123!')

        response = self.client.post(
            '/api/admin/users',
            data={
                'email': 'member@example.com',
                'password': 'AnotherStrongPass123!',
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 409)
