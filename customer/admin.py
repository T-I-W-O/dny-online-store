from django.contrib import admin

# Register your models here.
from .models import *
REGISTER = {Activities,Notice,Slide,Customer, Product,Order,ProductImage,ProductSize,ProductColor,Coupon,Color,Review,Order,Comment,Reply,PasswordResetCode,ShippingOrder,OrderDetail,GuestCustomer}
admin.site.register(REGISTER)