from decimal import Decimal

import pytest
from django.contrib.gis.geos import Point

from app.models import ArtisanShop, Category, Order, OrderItem, Product, User


@pytest.mark.xfail(strict=True)
def test_calculate_order_total(db):
    customer = User.objects.create_user(username='customer', password='pass', role=User.ROLE_CUSTOMER)
    artisan = User.objects.create_user(username='artisan', password='pass', role=User.ROLE_ARTISAN)
    shop = ArtisanShop.objects.create(owner=artisan, name='Test Shop', location=Point(0, 0))
    category = Category.objects.create(name='TestCat')
    product1 = Product.objects.create(
        shop=shop, name='Prod1', description='', price=Decimal('10.00'), quantity=100, category=category
    )
    product2 = Product.objects.create(
        shop=shop, name='Prod2', description='', price=Decimal('5.00'), quantity=100, category=category
    )
    order = Order.objects.create(customer=customer, shop=shop)
    OrderItem.objects.create(
        order=order, product=product1, quantity=2, unit_price=Decimal('10.00'), total_price=Decimal('20.00')
    )
    OrderItem.objects.create(
        order=order, product=product2, quantity=3, unit_price=Decimal('5.00'), total_price=Decimal('15.00')
    )
    assert order.calculate_total() == Decimal('35.00')
