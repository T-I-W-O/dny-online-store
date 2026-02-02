# customer/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages
from .models import  *
from django.db.models.signals import post_save
from django.db.models import Q
from django.urls import reverse

import datetime
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import Group
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models.fields.files import FileField

# signals.py
import sys
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import ImageField
from cloudinary.models import CloudinaryField
from cloudinary.uploader import destroy


@receiver(post_delete)
def delete_images_on_model_delete(sender, instance, **kwargs):
    # Avoid running during migrations or fixture loading
    if 'migrate' in sys.argv or 'loaddata' in sys.argv:
        return

    for field in sender._meta.get_fields():
        # 1) Handle CloudinaryField explicitly
        if isinstance(field, CloudinaryField):
            file_field = getattr(instance, field.name, None)
            if file_field and getattr(file_field, 'public_id', None):
                try:
                    destroy(file_field.public_id, invalidate=True)
                    print(f"✅ Deleted Cloudinary file: {file_field.public_id}")
                except Exception as e:
                    print(f"❌ Error deleting Cloudinary file: {e}")

        # 2) Handle normal ImageField (including ones using CloudinaryStorage)
        elif isinstance(field, ImageField):
            file_field = getattr(instance, field.name, None)
            if file_field and file_field.name and file_field.storage.exists(file_field.name):
                try:
                    file_field.delete(save=False)
                    print(f"✅ Deleted ImageField file: {file_field.name}")
                except Exception as e:
                    print(f"❌ Error deleting ImageField file: {e}")


@receiver(post_save, sender=ShippingOrder)
def notify_low_stock_cart_users(sender, instance, created, **kwargs):
    """
    Notify users or guests if any product in their cart has low stock.
    Triggered every time a ShippingOrder is saved.
    """
    # Loop through all products instead of using instance as product
    for product in Product.objects.all():
        if product.limit is not None and product.limit < 5:
            # Find all cart activities for this product
            activities = Activities.objects.filter(
                product=product,
                cart=True
            ).filter(Q(customer__isnull=False) | Q(guest_customer__isnull=False))

            for activity in activities:
                # Check if a similar notice already exists
                existing_notice = Notice.objects.filter(
                    notice__icontains=product.name,
                    customer=activity.customer if activity.customer else None,
                    guest_customer=activity.guest_customer if activity.guest_customer else None
                ).exists()

                if not existing_notice:
                    message = f"Your '{product.name}' in your cart is at risk of extinction, buy it now! 🦖"

                    Notice.objects.create(
                        notice=message,
                        url=reverse('view_cart') + f"#activity-{activity.id}",
                        customer=activity.customer if activity.customer else None,
                        guest_customer=activity.guest_customer if activity.guest_customer else None,
                        broadcast=False,
                        is_system=True
                    )

                    # ✅ Debug prints
                    if activity.customer:
                        print(f"[NOTICE SENT] To Customer '{activity.customer.user.username}': {message}")
                    elif activity.guest_customer:
                        print(f"[NOTICE SENT] To Guest '{activity.guest_customer.session_key}': {message}")

@receiver(user_logged_in)
def link_guest_orders_to_user(sender, user, request, **kwargs):
    print(f"📣 Signal Triggered: {user.username} just logged in")

    try:
        customer = Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        print("❌ No Customer linked to user")
        return

    # Loop through all guest customers to find one with matching email
    matching_guests = GuestCustomer.objects.filter(
        email__iexact=customer.email.strip()
    )

    if not matching_guests.exists():
        print("❌ No matching GuestCustomer by email")
        return

    for guest_customer in matching_guests:
        print(f"✅ Found matching GuestCustomer: {guest_customer.email}")

        # Transfer orders and data
        Order.objects.filter(guest_customer=guest_customer).update(customer=customer, guest_customer=None)
        ShippingOrder.objects.filter(guest_customer=guest_customer).update(customer=customer, guest_customer=None)
        Activities.objects.filter(guest_customer=guest_customer).update(customer=customer, guest_customer=None)

        guest_customer.delete()
        print(f"✅ GuestCustomer {guest_customer.email} transferred and deleted")

    messages.success(request, "Welcome back! Your previous guest orders have been linked.")



@receiver(post_save, sender=Product)
def notify_finished_or_low_goods(sender, instance, created, **kwargs):
    
    admin_group = Group.objects.get(name='admin')
    admin_users = admin_group.user_set.all()
    admin_customers = Customer.objects.filter(user__in=admin_users)

    # Loop through all products to check limits
    for product in Product.objects.all():
        # If product is finished
        if product.limit == 0:
            message = f"The product '{product.name}' has finished please restock!!"
            for admin in admin_customers:
                already_sent = Notice.objects.filter(
                    customer=admin,
                    notice=message,
                    is_system=True
                ).exists()
                if not already_sent:
                    Notice.objects.create(
                        customer=admin,
                        notice=message,
                        is_system=True
                    )

        # If product is low (≤ 5 and > 0)
        elif product.limit <= 5:
            message = f"The product '{product.name}' is low on stock ({product.limit} unit(s) remain)"
            for admin in admin_customers:
                already_sent = Notice.objects.filter(
                    customer=admin,
                    notice=message,
                    is_system=True
                ).exists()
                if not already_sent:
                    Notice.objects.create(
                        customer=admin,
                        notice=message,
                        is_system=True
                    )
