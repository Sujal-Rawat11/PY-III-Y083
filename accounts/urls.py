# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('activate/<email_token>/', views.activate_email, name='activate_email'),

    path('cart/', views.cart, name='cart'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),

    # NEW
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
]
