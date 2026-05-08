from django.contrib import admin
from .models import Product, ProductImage, Category, ContactMessage, Order, OrderItem, Cart


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'unit_price', 'quantity', 'size']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'metal', 'stone', 'price', 'stock', 'is_featured', 'is_active']
    list_filter   = ['is_active', 'is_featured', 'is_new_arrival', 'category', 'metal', 'stone']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ['order_number', 'full_name', 'email', 'total', 'payment_method', 'is_paid', 'status', 'created_at']
    list_filter   = ['status', 'is_paid', 'payment_method']
    search_fields = ['full_name', 'email', 'payment_id']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'submitted_at', 'is_read']
    list_filter  = ['is_read']
