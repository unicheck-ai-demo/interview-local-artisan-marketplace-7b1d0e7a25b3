# Local Artisan Marketplace

A production-grade Django REST platform for connecting local artisans and customers seeking handmade goods. Supports registration, shop/product management, secure multi-item order placement, geolocation-based product search, live inventory alerts, and artisan analytics.

## Data Model Overview
- **User**: Custom user model with role ('customer', 'artisan').
- **ArtisanShop**: Shop entity, linked to an artisan (User), includes location (PointField).
- **Category**: Product classification.
- **Product**: Item for sale, linked to shop & category, stores price, quantity, and geotag.
- **Order**: Placed by customer, linked to shop, supports status transitions.
- **OrderItem**: Line item for each order.
- **DeliverySchedule**: Linked to order for delivery info.
- **InventoryAlert**: Shop-level alert for low stock products; cached in Redis for performance.

## Core Features
- **User & Artisan Registration**: Register via `/api/register/` with role. Role governs permissions.
- **Product Catalog Management**: CRUD for products and categories. Products support geospatial filtering via `/api/products/geosearch/?lat=X&lng=Y&radius=R`.
- **Order Processing**: Multi-item ordering with transaction safety; supports secure fulfillment.
- **Inventory Alerts**: Auto-generated for low-stock products (quantity ≤ 3). Artisans retrieve via `/api/inventory-alerts/?shop=SHOP_ID`.
- **Store-Level Analytics**: Monthly revenue, category breakdown, top products (with window functions) via dashboard endpoint `/api/shops/{id}/dashboard/`.

## Advanced Features
- **Geolocation-Based Discovery**: Spatial queries with PostGIS for finding nearby handmade goods.
- **Multi-Step Transaction Order Fulfillment**: Inventory update is row-locked (select_for_update); errors roll back transaction.
- **Artisan Dashboard**: Aggregates KPIs with optimized ORM and annotated window function ranking.

## Architecture & Best Practices
- Layered architecture: Models, service layer, DRF endpoints.
- Business logic in `app/services.py`. Models in `app/models.py`. API entry points in `app/api/`.
- Transactional integrity: All order placement wrapped in atomic transaction.
- Caching: Redis used for inventory alerts.
- Authentication: Token & session. Most endpoints require authentication.
- API: Resource-based, documented via DRF patterns.

## Quick Usage
1. **Register**: `POST /api/register/` (`role`: 'customer' or 'artisan').
2. **Login**: Obtain token via login; use DRF auth header.
3. **Artisan Shop/Product Management**: CRUD via `/api/shops/`, `/api/products/`.
4. **Browse/Search**: `/api/products/` and `/api/products/geosearch/`.
5. **Order Placement**: `POST /api/orders/`.
6. **Inventory Alert**: `/api/inventory-alerts/?shop={SHOP_ID}`.
7. **Analytics/Dashboard**: `/api/shops/{id}/dashboard/` (artisan only).

## Testing
- Tests cover model, service layer, API endpoints, permissions and business rules.
- `make test` for full testing; `make lint` for style/format.

## Business Rules Enforced
- Only artisans may create shops/products.
- Inventory updates on order use select_for_update, atomic transaction.
- Low stock (≤ 3) triggers inventory alerts (cached/limited by Redis).
- Window function analytics for top products by revenue on dashboard.

## Technologies
- Django 4+, Django REST Framework, PostgreSQL/PostGIS, Redis, pytest, TokenAuthentication.
