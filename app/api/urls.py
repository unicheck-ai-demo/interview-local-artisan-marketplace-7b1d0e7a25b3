from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArtisanShopViewSet,
    CategoryViewSet,
    HealthCheckView,
    InventoryAlertViewSet,
    OrderViewSet,
    ProductViewSet,
    UserRegistrationView,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'shops', ArtisanShopViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'inventory-alerts', InventoryAlertViewSet, basename='inventory-alerts')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
]

app_name = 'api'
