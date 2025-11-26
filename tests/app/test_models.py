from django.contrib.gis.geos import Point

from app.models import ArtisanShop, User


def test_user_role_creation(db):
    user = User.objects.create_user(username='artisan', password='test', role=User.ROLE_ARTISAN)
    assert user.role == User.ROLE_ARTISAN


def test_artisan_shop_creation(db):
    user = User.objects.create_user(username='artisan2', password='test', role=User.ROLE_ARTISAN)
    shop = ArtisanShop.objects.create(owner=user, name='Test Shop', location=Point(12.49, 41.89))
    assert shop.owner == user
    assert shop.location.x == 12.49
    assert shop.location.y == 41.89
