from django.contrib.gis.geos import Point

from app.models import User
from app.services import (
    create_category,
    create_order,
    create_product,
    create_shop,
    create_user,
    get_shop_products,
)


def test_create_user_service(db):
    user = create_user('service_artisan', 'pw', User.ROLE_ARTISAN)
    assert user.username == 'service_artisan'
    assert user.role == User.ROLE_ARTISAN


def test_create_and_get_shop_products_service(db):
    artisan = create_user('artisan_for_services', 'pw', User.ROLE_ARTISAN)
    cat = create_category('Jewelry')
    shop = create_shop(artisan, 'RingSmiths', Point(10, 10))
    prod1 = create_product(shop, 'Silver Ring', 100, 5, cat, location=Point(10, 10))
    prod2 = create_product(shop, 'Gold Ring', 200, 3, cat, location=Point(10, 10))
    products = get_shop_products(shop)
    assert set(p.name for p in products) == {'Silver Ring', 'Gold Ring'}


def test_create_order_service(db):
    customer = create_user('customer', 'pw', User.ROLE_CUSTOMER)
    artisan = create_user('artisan_shop', 'pw', User.ROLE_ARTISAN)
    cat = create_category('Pottery')
    shop = create_shop(artisan, 'ClayWorks', Point(8, 8))
    prod = create_product(shop, 'Vase', 80, 2, cat, location=Point(8, 8))
    order = create_order(customer, shop, [{'product': prod, 'quantity': 1}])
    assert order.customer == customer
    assert order.shop == shop
    oi = order.items.first()
    assert oi.product == prod
    assert oi.quantity == 1
