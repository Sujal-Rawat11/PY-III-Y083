from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from base.emails import send_account_activation_email
from products.models import Coupon, Product, ColorVariant, SizeVariant


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile', null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        from accounts.models import CartItem  # avoid circular import
        return CartItem.objects.filter(cart__is_paid=False, cart__user=self.user).count()


@receiver(post_save, sender=User)
def create_profile_and_send_email(sender, instance, created, **kwargs):
    if created:
        email_token = str(uuid.uuid4())
        Profile.objects.create(user=instance, email_token=email_token)
        try:
            send_account_activation_email(instance.email, email_token)
        except Exception as e:
            print("Email sending failed:", e)


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Cart of {self.user.username}"

    # 🧾 Subtotal (before discount)
    def get_cart_subtotal(self):
        total = 0
        for cart_item in self.cart_items.all():
            price = cart_item.product.price
            if cart_item.color_variant:
                price += cart_item.color_variant.price
            if cart_item.size_variant:
                price += cart_item.size_variant.price
            total += price * cart_item.quantity
        return total

    # 💸 Discount (if coupon is applied)
    def get_discount_amount(self):
        subtotal = self.get_cart_subtotal()
        if self.coupon and not self.coupon.is_expired:
            return (subtotal * self.coupon.discount_percent) / 100
        return 0

    # ✅ Final total (after discount)
    def get_cart_total(self):
        return self.get_cart_subtotal() - self.get_discount_amount()


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size_variant = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        """Return (price + variant prices) × quantity"""
        price = self.product.price
        if self.color_variant:
            price += self.color_variant.price
        if self.size_variant:
            price += self.size_variant.price
        return price * self.quantity

    def __str__(self):
        return f"{self.product.product_name} (x{self.quantity}) in cart of {self.cart.user.username}"
