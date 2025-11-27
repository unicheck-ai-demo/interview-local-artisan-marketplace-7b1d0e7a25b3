from django.contrib.auth import get_user_model
from rest_framework import serializers

from app.models import ArtisanShop, Category, Order, Product
from app.services import create_order


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


class OrderSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    shop = ArtisanShopSerializer(read_only=True)
    shop_id = serializers.PrimaryKeyRelatedField(source='shop', queryset=ArtisanShop.objects.all(), write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'shop', 'shop_id', 'items', 'created_at', 'total_amount', 'status']
        read_only_fields = ['created_at', 'total_amount', 'status', 'customer', 'shop']

    def create(self, validated_data):
        request = self.context['request']
        customer = request.user
        shop = validated_data['shop']
        items_data = validated_data.pop('items')
        item_args = []
        for item in items_data:
            product_id = item.get('product_id')
            if not product_id:
                raise serializers.ValidationError('product_id is required for each item')
            product = Product.objects.get(pk=product_id)
            quantity = item.get('quantity')
            if not quantity or quantity < 1:
                raise serializers.ValidationError('quantity must be >= 1 for each item')
            item_args.append({'product': product, 'quantity': quantity})
        try:
            order = create_order(customer, shop, item_args)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        return order
