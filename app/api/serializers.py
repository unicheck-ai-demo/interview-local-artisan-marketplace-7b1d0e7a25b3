from django.contrib.auth import get_user_model
from rest_framework import serializers

from app.models import ArtisanShop, Category, Order, OrderItem, Product


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'role', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', get_user_model().ROLE_CUSTOMER),
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ArtisanShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtisanShop
        fields = ['id', 'owner', 'name', 'description', 'location', 'created_at']
        read_only_fields = ['owner', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'shop',
            'name',
            'description',
            'price',
            'quantity',
            'category',
            'category_id',
            'location',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'shop']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'unit_price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    shop = ArtisanShopSerializer(read_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(source='shop', queryset=ArtisanShop.objects.all(), write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'shop', 'shop_id', 'items', 'created_at', 'total_amount', 'status']
        read_only_fields = ['created_at', 'total_amount', 'status', 'customer', 'shop']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(customer=self.context['request'].user, shop=validated_data['shop'])
        total_amount = 0
        for item in items_data:
            product = item['product']
            quantity = item['quantity']
            unit_price = product.price
            total_price = unit_price * quantity
            OrderItem.objects.create(
                order=order, product=product, quantity=quantity, unit_price=unit_price, total_price=total_price
            )
            total_amount += total_price
        order.total_amount = total_amount
        order.save()
        return order
