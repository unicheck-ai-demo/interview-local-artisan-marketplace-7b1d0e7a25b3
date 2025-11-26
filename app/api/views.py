from django.db import DatabaseError, connection
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from app.api.serializers import (
    ArtisanShopSerializer,
    CategorySerializer,
    OrderSerializer,
    ProductSerializer,
    UserSerializer,
)
from app.models import ArtisanShop, Category, Order, Product, User


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ArtisanShopViewSet(viewsets.ModelViewSet):
    queryset = ArtisanShop.objects.all()
    serializer_class = ArtisanShopSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('shop', 'category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        shop_id = self.request.data.get('shop')
        shop = ArtisanShop.objects.get(id=shop_id)
        serializer.save(shop=shop)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items').select_related('shop', 'customer').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


class HealthCheckView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT PostGIS_Full_Version();')
                cursor.fetchone()
        except DatabaseError as e:
            return Response({'status': 'error', 'db': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
