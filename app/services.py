from .models import ArtisanShop, Category, Order, OrderItem, Product, User


def create_user(username, password, role):
    user = User.objects.create_user(username=username, password=password, role=role)
    return user


def create_category(name, description=None):
    return Category.objects.create(name=name, description=description)


def create_shop(owner, name, location=None, description=None):
    shop = ArtisanShop.objects.create(owner=owner, name=name, description=description, location=location)
    return shop


def create_product(shop, name, price, quantity, category, location=None, description=None):
    product = Product.objects.create(
        shop=shop,
        name=name,
        price=price,
        quantity=quantity,
        category=category,
        location=location,
        description=description,
    )
    return product


def get_shop_products(shop):
    return Product.objects.filter(shop=shop)


def create_order(customer, shop, items):
    total_amount = sum(item['product'].price * item['quantity'] for item in items)
    order = Order.objects.create(customer=customer, shop=shop, total_amount=total_amount)
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
            unit_price=item['product'].price,
            total_price=item['product'].price * item['quantity'],
        )
    return order


def get_order(order_id):
    return Order.objects.prefetch_related('items').get(pk=order_id)
