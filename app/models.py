from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as geomodels
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CUSTOMER = 'customer'
    ROLE_ARTISAN = 'artisan'
    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_ARTISAN, 'Artisan'),
    ]
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_CUSTOMER, db_index=True)

    def is_artisan(self):
        return self.role == self.ROLE_ARTISAN

    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ArtisanShop(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    location = geomodels.PointField(srid=4326, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        unique_together = [('owner', 'name')]

    def __str__(self):
        return self.name


class Product(models.Model):
    shop = models.ForeignKey(ArtisanShop, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    location = geomodels.PointField(srid=4326, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.shop.name})'


class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    shop = models.ForeignKey(ArtisanShop, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    def __str__(self):
        return f'Order {self.pk} by {self.customer.username} ({self.shop.name})'

    # The following method contains a bug: it incorrectly calculates the total order amount
    def calculate_total(self):
        return sum(item.unit_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'


class DeliverySchedule(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_schedule')
    scheduled_date = models.DateTimeField(null=True, blank=True)
    address = models.CharField(max_length=255)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Delivery for order {self.order.pk}'


class InventoryAlert(models.Model):
    shop = models.ForeignKey(ArtisanShop, on_delete=models.CASCADE, related_name='inventory_alerts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='alerts')
    triggered_at = models.DateTimeField(default=timezone.now)
    quantity = models.PositiveIntegerField()
    resolved = models.BooleanField(default=False)

    class Meta:
        unique_together = [('shop', 'product', 'triggered_at')]

    def __str__(self):
        return f'Low stock alert for {self.product.name} in {self.shop.name}'
