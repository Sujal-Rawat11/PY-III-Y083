from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST

from .models import Profile, Cart, CartItem
from products.models import Coupon


# ---------------------- AUTH VIEWS ----------------------

def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username=email)

        if not user_obj.exists():
            messages.warning(request, 'Account not found.')
            return redirect('accounts:login')

        if not user_obj[0].profile.is_email_verified:
            messages.warning(request, 'Your account is not verified.')
            return redirect('accounts:login')

        user_obj = authenticate(username=email, password=password)
        if user_obj:
            login(request, user_obj)
            return redirect('/')

        messages.warning(request, 'Invalid credentials')
        return redirect('accounts:login')

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=email).exists():
            messages.warning(request, 'Email is already taken.')
            return redirect('accounts:register')

        user_obj = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email
        )
        user_obj.set_password(password)
        user_obj.save()

        messages.success(request, 'An email has been sent for verification.')
        return redirect('accounts:register')

    return render(request, 'accounts/register.html')


def activate_email(request, email_token):
    try:
        profile = Profile.objects.get(email_token=email_token)
        profile.is_email_verified = True
        profile.save()
        messages.success(request, 'Your email has been verified successfully!')
        return redirect('/')
    except Profile.DoesNotExist:
        return HttpResponse('Invalid email token')


# ---------------------- CART VIEWS ----------------------

@login_required
def cart(request):
    """Show cart, handle coupon form, and display totals."""
    cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
    cart_items = cart_obj.cart_items.all()

    subtotal = sum(item.get_total_price() for item in cart_items)
    discount = 0
    total = subtotal

    # Handle coupon submission
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon', '').strip()
        if not coupon_code:
            messages.warning(request, 'Please enter a coupon code.')
            return redirect('accounts:cart')

        coupon_obj = Coupon.objects.filter(coupon_code__iexact=coupon_code, is_expired=False).first()
        if not coupon_obj:
            messages.warning(request, 'Invalid or expired coupon.')
            return redirect('accounts:cart')

        if subtotal < coupon_obj.minimum_amount:
            messages.warning(request, f'Minimum order amount for this coupon is ₹{coupon_obj.minimum_amount}.')
            return redirect('accounts:cart')

        cart_obj.coupon = coupon_obj
        cart_obj.save()
        messages.success(request, f'Coupon "{coupon_code}" applied successfully!')
        return redirect('accounts:cart')

    # Calculate totals if coupon already applied
    if cart_obj.coupon and not cart_obj.coupon.is_expired:
        discount = (subtotal * cart_obj.coupon.discount_percent) / 100
        total = subtotal - discount

    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
        'total_price': subtotal,
        'discount_amount': discount,
        'total_price_with_discount': total,
        'quantity_options': range(1, 6),
    }
    return render(request, 'accounts/cart.html', context)


@require_POST
@login_required
def apply_coupon(request):
    """Alternative coupon handler (used if coupon form action is separate)."""
    coupon_code = request.POST.get('coupon', '').strip()
    if not coupon_code:
        messages.warning(request, 'Please enter a coupon code.')
        return redirect('accounts:cart')

    cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
    coupon_obj = Coupon.objects.filter(coupon_code__iexact=coupon_code, is_expired=False).first()

    if not coupon_obj:
        messages.warning(request, 'Invalid or expired coupon.')
        return redirect('accounts:cart')

    subtotal = sum(item.get_total_price() for item in cart_obj.cart_items.all())
    if subtotal < coupon_obj.minimum_amount:
        messages.warning(request, f'Minimum order amount is ₹{coupon_obj.minimum_amount}.')
        return redirect('accounts:cart')

    cart_obj.coupon = coupon_obj
    cart_obj.save()
    messages.success(request, f'Coupon "{coupon_code}" applied successfully!')
    return redirect('accounts:cart')


@login_required
def update_cart_item(request, item_id):
    """Handles quantity update directly from dropdown."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__is_paid=False)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, f"Quantity updated to {quantity}.")
            else:
                messages.warning(request, "Quantity must be at least 1.")
        except ValueError:
            messages.warning(request, "Invalid quantity selected.")

    return redirect("accounts:cart")


@login_required
def remove_cart_item(request, item_id):
    """Removes an item from the user's cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user, cart__is_paid=False)
    if request.method == "POST":
        cart_item.delete()
        messages.success(request, f"'{cart_item.product.product_name}' removed from cart.")
    return redirect("accounts:cart")
