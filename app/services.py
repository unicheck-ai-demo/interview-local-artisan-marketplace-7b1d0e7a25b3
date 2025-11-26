import redis
from django.conf import settings
from django.db import transaction
from django.db.models import F, Sum, Window
from django.db.models.functions import Rank

from .models import InventoryAlert, Order, OrderItem, Product

redis_client = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])


def create_order(customer, shop, items):
    with transaction.atomic():
        total_amount = 0
        created_items = []
        order = Order.objects.create(customer=customer, shop=shop, total_amount=0)
        for item in items:
            product = Product.objects.select_for_update().get(pk=item['product'].pk)
            if product.quantity < item['quantity']:
                raise ValueError(f'Insufficient inventory for product {product.name}')
            product.quantity = F('quantity') - item['quantity']
            product.save()
            product.refresh_from_db()
            unit_price = product.price
            total_price = unit_price * item['quantity']
            oi = OrderItem.objects.create(
                order=order, product=product, quantity=item['quantity'], unit_price=unit_price, total_price=total_price
            )
            created_items.append(oi)
            total_amount += total_price
            if product.quantity <= 3:
                _trigger_inventory_alert(shop, product)
        order.total_amount = total_amount
        order.save()
        return order


def _trigger_inventory_alert(shop, product):
    alert_key = f'inventory-alert:{shop.id}:{product.id}'
    if not redis_client.get(alert_key):
        InventoryAlert.objects.create(shop=shop, product=product, quantity=product.quantity)
        redis_client.setex(alert_key, 3600, 'alert')


def get_inventory_alerts(shop):
    return InventoryAlert.objects.filter(shop=shop, resolved=False)


def geolocation_product_search(point, radius_km=10, category=None):
    filter_qs = Product.objects.filter(location__distance_lte=(point, radius_km * 1000))
    if category:
        filter_qs = filter_qs.filter(category=category)
    return filter_qs.select_related('shop', 'category')


def monthly_sales_analytics(shop, month=None, year=None):
    sales_qs = Order.objects.filter(shop=shop, status=Order.STATUS_COMPLETED)
    if month and year:
        sales_qs = sales_qs.filter(created_at__year=year, created_at__month=month)
    items_qs = OrderItem.objects.filter(order__in=sales_qs)
    total_revenue = items_qs.aggregate(revenue=Sum('total_price'))['revenue'] or 0
    category_revenue = items_qs.values('product__category__name').annotate(revenue=Sum('total_price'))
    top_products = (
        items_qs.values('product__id', 'product__name')
        .annotate(
            product_revenue=Sum('total_price'),
            product_count=Sum('quantity'),
            rank=Window(Rank(), order_by=F('product_revenue').desc()),
        )
        .order_by('-product_revenue')[:5]
    )
    return {
        'total_revenue': total_revenue,
        'category_revenue': list(category_revenue),
        'top_products': list(top_products),
    }


def artisan_dashboard_kpis(shop):
    analytics = monthly_sales_analytics(shop)
    total_completed_orders = Order.objects.filter(shop=shop, status=Order.STATUS_COMPLETED).count()
    low_stock_products = Product.objects.filter(shop=shop, quantity__lte=3).values('id', 'name', 'quantity')
    alerts = get_inventory_alerts(shop)
    return {
        'monthly_analytics': analytics,
        'completed_orders': total_completed_orders,
        'low_stock_products': list(low_stock_products),
        'active_alerts': alerts.count(),
    }
