from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Cart, CartItem
from .models import Product, SizeVariant

# ---------------------------
# Product detail page
# ---------------------------
def get_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    size_variants = SizeVariant.objects.filter(product=product)

    cart = None
    if request.user.is_authenticated:
        cart_qs = Cart.objects.filter(user=request.user, is_paid=False)
        if cart_qs.exists():
            cart = cart_qs.first()

    context = {
        'product': product,
        'size_variants': size_variants,
        'cart': cart,
    }
    return render(request, 'product/product.html', context)


# ---------------------------
# Add to cart
# ---------------------------
@login_required
def add_to_cart(request, uid):
    product = get_object_or_404(Product, uid=uid)
    user = request.user
    variant = request.GET.get('variant')

    cart, _ = Cart.objects.get_or_create(user=user, is_paid=False)
    cart_item = CartItem.objects.create(cart=cart, product=product)

    if variant:
        try:
            size_variant = SizeVariant.objects.get(size_name=variant)
            cart_item.size_variant = size_variant
            cart_item.save()
        except SizeVariant.DoesNotExist:
            messages.warning(request, "Invalid size selected.")

    messages.success(request, f"{product.product_name} added to cart!")
    return redirect('cart')


