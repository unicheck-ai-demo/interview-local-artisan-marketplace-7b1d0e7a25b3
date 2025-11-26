import pytest
from django.urls import reverse
from rest_framework import status

from app.models import ArtisanShop, Category, Product, User

pytestmark = pytest.mark.django_db


def test_user_registration(api_client):
    url = reverse('api:user-register')
    data = {
        'username': 'artisanapi',
        'password': 'pw123456',
        'role': User.ROLE_ARTISAN,
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username='artisanapi').exists()


def test_product_list(api_client, user):
    category = Category.objects.create(name='Woodwork')
    shop = ArtisanShop.objects.create(owner=user, name='Wooden Wonders')
    Product.objects.create(shop=shop, name='Table', price=300, quantity=2, category=category)
    url = reverse('api:product-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['results'][0]['name'] == 'Table'
