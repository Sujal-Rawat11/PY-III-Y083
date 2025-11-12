from django.db import models
from django.utils import timezone  
from base.models import BaseModel
from django.utils.text import slugify


class Category(BaseModel):
    category_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank = True)
    category_image = models.ImageField(upload_to="categories")


    def save(self , *args, **kwargs):
        self.slug = slugify(self.category_name)
        super(Category , self).save(*args, **kwargs)


    def __str__(self) -> str:
        return self.category_name
    



class ColorVariant(BaseModel):
    color_name = models.CharField(max_length=100)
    price = models.IntegerField(default =0)

    def __str__(self)->str:
        return self.color_name

class SizeVariant(BaseModel):
    size_name = models.CharField(max_length = 100)
    price = models.IntegerField(default = 0)

    def __str__(self)->str:
        return self.size_name



class Product(BaseModel):
    product_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.FloatField()
    product_description = models.TextField()
    slug = models.SlugField(unique=True, null=True, blank=True)
    color_variant  = models.ManyToManyField(ColorVariant, null = True, blank = True)
    size_variant = models.ManyToManyField(SizeVariant, null = True , blank = True)



    def save(self , *args, **kwargs):
        self.slug = slugify(self.product_name)
        super(Product , self).save(*args, **kwargs)


    def __str__(self) -> str:
        return self.product_name
    
    def get_product_price_by_size(self, size):
        try:
            size_obj = self.size_variant.get(size_name=size)
            return self.price + size_obj.price
        except SizeVariant.DoesNotExist:
            return self.price






class ProductImage(BaseModel):
    product = models.ForeignKey(Product , on_delete=models.CASCADE , related_name = "product_images")
    image = models.ImageField(upload_to="product")


class Coupon(models.Model):
    coupon_code = models.CharField(max_length=50, unique=True)
    discount_price = models.PositiveIntegerField(default=0, help_text="Discount amount in rupees or percent")
    minimum_amount = models.PositiveIntegerField(default=0, help_text="Minimum order value required for this coupon")
    is_expired = models.BooleanField(default=False)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.coupon_code

    def is_valid(self):
        """
        Check if coupon is still valid based on date and flag.
        """
        now = timezone.now()
        if self.is_expired:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True

    def get_discount_amount(self, total):
        """
        Returns discount based on total amount.
        If 'discount_price' is <= 100, treat it as percentage.
        Otherwise, treat it as flat discount in ₹.
        """
        if not self.is_valid() or total < self.minimum_amount:
            return 0
        if self.discount_price <= 100:
            return (total * self.discount_price) / 100
        return self.discount_price