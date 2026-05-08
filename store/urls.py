from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/paypal-capture/', views.paypal_capture, name='paypal_capture'),
    path('order/<int:pk>/confirmed/', views.order_confirm, name='order_confirm'),
    path('orders/', views.order_history, name='order_history'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Superuser Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/messages/', views.messages_view, name='messages'),
    path('dashboard/product/add/', views.product_add, name='product_add'),
    path('dashboard/product/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('dashboard/product/<int:pk>/toggle/', views.product_toggle, name='product_toggle'),
    path('dashboard/order/<int:pk>/', views.order_detail_admin, name='order_detail_admin'),
]
