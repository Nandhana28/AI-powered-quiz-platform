import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestRegisterView:
    def test_register_success(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'username':         'newuser',
            'email':            'newuser@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
        }, format='json')
        assert response.status_code == 201
        assert response.data['success'] is True

    def test_register_duplicate_email(self, api_client, test_user):
        response = api_client.post('/api/v1/auth/register/', {
            'username':         'another',
            'email':            test_user.email,
            'password':         'Test1234!',
            'confirm_password': 'Test1234!',
        }, format='json')
        assert response.status_code == 400

    def test_register_password_mismatch(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'username':         'newuser',
            'email':            'new@test.com',
            'password':         'Test1234!',
            'confirm_password': 'Wrong1234!',
        }, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    def test_login_success(self, api_client, test_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email':    test_user.email,
            'password': 'Test1234!',
        }, format='json')
        assert response.status_code == 200
        assert 'access' in response.data['data']
        assert 'refresh' in response.data['data']

    def test_login_wrong_password(self, api_client, test_user):
        response = api_client.post('/api/v1/auth/login/', {
            'email':    test_user.email,
            'password': 'WrongPass!',
        }, format='json')
        assert response.status_code == 401