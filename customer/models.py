from django.db import models
import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator,MaxValueValidator
from django.core.exceptions import ValidationError
from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary.models import CloudinaryField

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    username = models.CharField(max_length=100, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    number = models.CharField(max_length=15)
    email = models.EmailField(max_length=100)
    image = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='profile/', default='default_image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class GuestCustomer(models.Model):
    session_key = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name or 'Guest'} {self.last_name or ''} (Guest)"


class Product(models.Model):
    STATUS_CHOICES = [
        ('Sold', 'Sold'),
        ('New', 'New'),
        ('Discount', 'Discount'),
        
    ]
    CATEGORY_CHOICES = [
        ('Wig', 'Wig'),
        ('Perfume', 'Perfume'),
        ('Shoe', 'Shoe'),
        ('Cloth', 'Cloth'),
        ('Bag', 'Bag'),
        ('Others', 'Others'),
    ]

    name = models.CharField(max_length=100, null=True)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    limit = models.IntegerField(null=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, null=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        
        return f"{self.name} - {self.category}"
    
    def is_new(self):
        """
        Returns True if the product is within 7 days of being created.
        """
        if not self.created_at:
            return False
        return (timezone.now().date() - self.created_at).days <= 7





class ProductImage(models.Model):
    TYPE = [
        ('Main', 'Main'),
        ('Other', 'Other'),
        
    ]
    type = models.CharField(max_length=20, choices=TYPE,  default='Main')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(storage=MediaCloudinaryStorage(),upload_to='products')

    def __str__(self):
        return f"{self.type} image for {self.product.name}"





class Color(models.Model):
   
    color_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.color_name}"


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='size_variants')
    size = models.CharField(max_length=50)
    colors = models.ManyToManyField('Color')  # I assume you meant 'Color' here

    def __str__(self):
        return f"{self.product.name} - Size {self.size}"


class ProductColor(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color_variants', null=True, blank=True) 
    colors = models.ManyToManyField('Color')  # Same here

    def __str__(self):
        return f"{self.product.name} - Color Variant"

    

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=0, choices=[(i, str(i)) for i in range(6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer.user.username} for {self.product.name} ({self.rating}/5)"

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    guest_customer = models.ForeignKey(GuestCustomer, on_delete=models.CASCADE, null=True, blank=True)
    total_price = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    quantity = models.IntegerField(default=1)
    date = models.DateField(auto_now_add=True)
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refundeded'),
    ]
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='Pending'
    )
    
    STATUS_CHOICES = [
        ('Delivered', 'Delivered'),
        ('Ongoing', 'Ongoing'),
        ('Inactive', 'Inactive'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Inactive'
    )
    
    transaction_id = models.CharField(max_length=200, null=True)

    def __str__(self):
        if self.customer:
            name = self.customer.user.username
        elif self.guest_customer:
            name = f"{self.guest_customer.first_name} (Guest)"
        else:
            name = "Unknown"

        return f"Order of {self.product.name} by {name}"

    

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='details')
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, null=True)
    colors = models.ManyToManyField(Color)


    def __str__(self):
        customer_name = None
        if self.order.customer:
            customer_name = self.order.customer.user.username
        elif self.order.guest_customer:
            customer_name = f"{self.order.guest_customer.first_name} (Guest)"
        else:
            customer_name = "Unknown"

        product_name = self.order.product.name if self.order.product else "Unknown Product"

        return f"Size and colors for order of {product_name} by {customer_name}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_percent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    one_time_use = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    used_by_customer = models.ManyToManyField(Customer, blank=True)
    used_by_guest = models.ManyToManyField(GuestCustomer, blank=True)

    def __str__(self):
        return f"{self.code} - {'%' if self.is_percent else '₦'}{self.amount}"

class ShippingOrder(models.Model):
    MODE_CHOICES = [
        ('Delivery', 'Delivery'),
        ('Pickup', 'Pickup'),
    ]

    SAVE_CHOICES = [
        ('Save', 'Save'),
        ('Unsave', 'Unsave'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    guest_customer = models.ForeignKey(GuestCustomer, on_delete=models.CASCADE, null=True, blank=True)
    orders = models.ManyToManyField(Order)
    
    # New field: Link to Coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)

    address = models.CharField(max_length=100, default='', null=True)
    country = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    town = models.CharField(max_length=100, null=True)
    local_government = models.CharField(max_length=100, null=True)

    deliverydate = models.DateTimeField(null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    order_note = models.TextField(null=True, blank=True)

    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='Delivery')
    save_status = models.CharField(max_length=10, choices=SAVE_CHOICES, default='Unsave')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.customer:
            name = self.customer.first_name
        elif self.guest_customer:
            name = f"{self.guest_customer.first_name} (Guest)"
        else:
            name = "Unknown"

        item_count = self.orders.count()
        return f"{name}'s Shipping Order ({item_count} item{'s' if item_count != 1 else ''})"





class Notice(models.Model):
    notice = models.TextField(blank=True, null=True, default='')
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name='received_notices')
    guest_customer = models.ForeignKey(GuestCustomer, null=True, blank=True, on_delete=models.CASCADE, related_name='received_notices')
    from_customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_notices')
    from_guest_customer = models.ForeignKey(GuestCustomer, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_notices')
    broadcast = models.BooleanField(default=False)
    read = models.BooleanField(default=False)  # Add this line
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ THIS LINE
    expiry = models.DateTimeField(default=timezone.now)  # ✅ THIS LINE
    is_system = models.BooleanField(default=False)
    url = models.CharField(null=True, blank=True, max_length=100)

    def __str__(self):
        return self.notice



class Slide(models.Model):
    image = models.ImageField(storage=MediaCloudinaryStorage(), upload_to='slides/', blank=True, null=True)
    title = models.CharField(max_length=20, null=True)
    description = models.CharField(max_length=60, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



class Activities(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    guest_customer = models.ForeignKey("GuestCustomer", on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    cart = models.BooleanField(default=False)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=20, null=True, blank=True)
    selected_size = models.CharField(max_length=50, null=True, blank=True)
    selected_color = models.CharField(max_length=50, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        if self.customer:
            name = self.customer.username
        elif self.guest_customer:
            name = f"{self.guest_customer.first_name or 'Guest'} (Guest)"
        else:
            name = "Unknown User"

        product_name = self.product.name if self.product else "Unknown Product"
        return f"{name} - {product_name}"



class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    guest_customer = models.ForeignKey("GuestCustomer", on_delete=models.CASCADE, null=True, blank=True)
    time = models.DateTimeField(default=timezone.now)
    rating = models.PositiveSmallIntegerField(
    validators=[MinValueValidator(1), MaxValueValidator(5)],
    null=True, blank=True
)
    comment =  models.TextField()

    def __str__(self):
        if self.customer:
            name = self.customer.username
        elif self.guest_customer:
            name = f"{self.guest_customer.first_name or 'Guest'} (Guest)"
        else:
            name = "Unknown User"
        return f" {self.comment}-{name} - {self.product.name} "


class Reply(models.Model):
    comment = models.ForeignKey(Comment, related_name="replies", on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    guest_customer = models.ForeignKey("GuestCustomer", on_delete=models.CASCADE, null=True, blank=True)
    replying_customer = models.ForeignKey(Customer, related_name='replied_to', on_delete=models.SET_NULL, null=True, blank=True)  # ✅ ADD THIS
    replying_guest = models.ForeignKey("GuestCustomer", related_name='replied_to', on_delete=models.SET_NULL, null=True, blank=True)  # ✅ ADD THIS
    time = models.DateTimeField(default=timezone.now)
    reply = models.TextField()

    def __str__(self):
        return f"{self.comment.comment} - {self.reply}"


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + datetime.timedelta(minutes=10)


class Visitor(models.Model):
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    guest_customer = models.ForeignKey(GuestCustomer, on_delete=models.SET_NULL, null=True, blank=True)
    visited_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.session_key} at {self.visited_at}"


