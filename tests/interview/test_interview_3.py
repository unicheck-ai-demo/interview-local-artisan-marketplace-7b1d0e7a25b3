from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from app.models import ArtisanShop, Category, Product

pytestmark = pytest.mark.django_db


@pytest.mark.xfail(strict=True)
def test_recommendations_simple(api_client, user):
    category = Category.objects.create(name='Cat1')
    shop = ArtisanShop.objects.create(owner=user, name='Shop1')
    main = Product.objects.create(shop=shop, name='Main', price=Decimal('10.00'), quantity=10, category=category)
    p1 = Product.objects.create(shop=shop, name='P1', price=Decimal('5.00'), quantity=5, category=category)
    p2 = Product.objects.create(shop=shop, name='P2', price=Decimal('7.00'), quantity=7, category=category)
    other_cat = Category.objects.create(name='Cat2')
    Product.objects.create(shop=shop, name='P3', price=Decimal('9.00'), quantity=9, category=other_cat)
    url = reverse('api:product-recommendations', kwargs={'pk': main.id})
    response = api_client.get(url)
    assert response.status_code == 200
    names = {item['name'] for item in response.data}
    assert names == {'P1', 'P2'}


@pytest.mark.xfail(strict=True)
def test_recommendations_flash_sale_priority(api_client, user):
    category = Category.objects.create(name='Cat3')
    shop = ArtisanShop.objects.create(owner=user, name='Shop2')
    main = Product.objects.create(shop=shop, name='Main2', price=Decimal('10.00'), quantity=10, category=category)
    now = timezone.now()
    sale = Product.objects.create(
        shop=shop,
        name='SaleProd',
        price=Decimal('5.00'),
        quantity=5,
        category=category,
        flash_sale_price=Decimal('4.00'),
        flash_sale_start=now - timedelta(days=1),
        flash_sale_end=now + timedelta(days=1),
    )
    regular = Product.objects.create(
        shop=shop, name='RegularProd', price=Decimal('6.00'), quantity=6, category=category
    )
    url = reverse('api:product-recommendations', kwargs={'pk': main.id})
    response = api_client.get(url)
    assert response.status_code == 200
    names = [item['name'] for item in response.data]
    assert names[0] == 'SaleProd'
    assert names[1] == 'RegularProd'
