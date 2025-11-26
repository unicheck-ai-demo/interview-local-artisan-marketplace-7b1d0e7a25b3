from django.contrib.gis.geos import Point
from django.db import DatabaseError, connection
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
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
from app.services import (
    artisan_dashboard_kpis,
    geolocation_product_search,
    get_inventory_alerts,
)


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

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard(self, request, pk=None):
        shop = self.get_object()
        data = artisan_dashboard_kpis(shop)
        return Response(data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('shop', 'category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        shop_id = self.request.data.get('shop')
        shop = ArtisanShop.objects.get(id=shop_id)
        serializer.save(shop=shop)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def geosearch(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        category_id = request.query_params.get('category')
        if not lat or not lng:
            return Response({'error': 'Missing latitude/longitude'}, status=status.HTTP_400_BAD_REQUEST)
        point = Point(float(lng), float(lat), srid=4326)
        category = None
        if category_id:
            Category.objects.filter(pk=category_id).first()
        products = geolocation_product_search(point, radius, category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items').select_related('shop', 'customer').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)


class InventoryAlertViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        shop_id = request.query_params.get('shop')
        shop = ArtisanShop.objects.filter(pk=shop_id).first()
        if not shop:
            return Response({'error': 'Invalid shop id'}, status=status.HTTP_400_BAD_REQUEST)
        alerts = get_inventory_alerts(shop)
        return Response(
            [
                {'id': a.id, 'product': a.product.name, 'quantity': a.quantity, 'triggered_at': a.triggered_at}
                for a in alerts
            ]
        )


class HealthCheckView(APIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT PostGIS_Full_Version();')
                cursor.fetchone()
        except DatabaseError as e:
            return Response({'status': 'error', 'db': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
