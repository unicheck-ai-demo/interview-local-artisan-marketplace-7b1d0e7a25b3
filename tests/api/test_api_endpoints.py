import pytest
from django.contrib.gis.geos import Point
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


def test_token_obtain(api_client, user):
    url = reverse('api:api-token')
    response = api_client.post(url, {'username': user.username, 'password': 'password123'})
    assert response.status_code == status.HTTP_200_OK
    assert 'token' in response.data


def test_product_list(api_client, user):
    category = Category.objects.create(name='Woodwork')
    shop = ArtisanShop.objects.create(owner=user, name='Wooden Wonders')
    Product.objects.create(shop=shop, name='Table', price=300, quantity=2, category=category)
    url = reverse('api:product-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['results'][0]['name'] == 'Table'


def test_shop_create_requires_auth(api_client):
    url = reverse('api:artisanshop-list')
    data = {'name': 'Test Shop'}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_shop_create_authenticated(authenticated_api_client, user):
    url = reverse('api:artisanshop-list')
    data = {'name': 'Test Shop'}
    response = authenticated_api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert ArtisanShop.objects.filter(name='Test Shop', owner=user).exists()


def test_inventory_alert_trigger(authenticated_api_client, user):
    category = Category.objects.create(name='Paintings')
    shop = ArtisanShop.objects.create(owner=user, name='Art House')
    product = Product.objects.create(shop=shop, name='Canvas', price=200, quantity=5, category=category)
    token_url = reverse('api:api-token')
    token_resp = authenticated_api_client.post(token_url, {'username': user.username, 'password': 'password123'})
    authenticated_api_client.credentials(HTTP_AUTHORIZATION=f'Token {token_resp.data["token"]}')
    order_url = reverse('api:order-list')
    order_data = {'shop_id': shop.id, 'items': [{'product_id': product.id, 'quantity': 3}]}
    order_resp = authenticated_api_client.post(order_url, order_data, format='json')
    assert order_resp.status_code == status.HTTP_201_CREATED
    product.refresh_from_db()
    assert product.quantity == 2
    # Place another order to trigger alert
    order_data2 = {'shop_id': shop.id, 'items': [{'product_id': product.id, 'quantity': 2}]}
    order_resp2 = authenticated_api_client.post(order_url, order_data2, format='json')
    assert order_resp2.status_code == status.HTTP_201_CREATED
    # should trigger alert
    alerts_url = reverse('api:inventory-alerts-list') + f'?shop={shop.id}'
    alerts_resp = authenticated_api_client.get(alerts_url)
    assert alerts_resp.status_code == status.HTTP_200_OK
    assert len(alerts_resp.data) >= 1
    assert alerts_resp.data[0]['product'] == 'Canvas'


def test_geosearch(authenticated_api_client, user):
    category = Category.objects.create(name='Pottery')
    shop = ArtisanShop.objects.create(owner=user, name='GeoShop', location=Point(8.0, 8.0))
    Product.objects.create(shop=shop, name='Mug', price=10, quantity=10, category=category, location=Point(8.0, 8.0))
    url = reverse('api:product-geosearch') + '?lat=8.0&lng=8.0&radius=10&category={}'.format(category.id)
    resp = authenticated_api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) > 0
    assert resp.data[0]['name'] == 'Mug'


def test_dashboard(authenticated_api_client, user):
    category = Category.objects.create(name='Glass')
    shop = ArtisanShop.objects.create(owner=user, name='Metrics Shop')
    Product.objects.create(shop=shop, name='Bottle', price=10, quantity=10, category=category)
    url = reverse('api:artisanshop-dashboard', kwargs={'pk': shop.id})
    resp = authenticated_api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert 'monthly_analytics' in resp.data
    assert 'completed_orders' in resp.data
