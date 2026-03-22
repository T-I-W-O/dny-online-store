# customer/signals.py

import datetime
import sys
import os

from decouple import config

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.db.models import Q, ImageField
from django.db.models.fields.files import FileField
from django.db.models.signals import post_save, post_delete, post_migrate
from django.urls import reverse
from django.utils import timezone

from cloudinary.models import CloudinaryField
from cloudinary.uploader import destroy
import cloudinary.uploader

from .models import *

def debug(msg):
    print(f"🐞 [DEBUG] {msg}")

@receiver(post_migrate)
def setup_roles(sender, **kwargs):
    # Only run once, when your app is migrated
    if sender.name != 'customer':  # Replace 'customer' with your app name
        return

    debug("🚀 Starting Superuser & Group setup...")
    User = get_user_model()

    # 1. Ensure Groups exist
    admin_group, _ = Group.objects.get_or_create(name='admin')
    customer_group, _ = Group.objects.get_or_create(name='customer')
    debug("Groups ensured: admin and customer")

    # Give all permissions to admin group (optional)
    if not admin_group.permissions.exists():
        admin_group.permissions.set(Permission.objects.all())
        debug("Permissions bound to admin group.")

    # 2. Get Superuser credentials from env
    username = config("DJANGO_SU_USERNAME", default=None)
    email = config("DJANGO_SU_EMAIL", default=None)
    password = config("DJANGO_SU_PASSWORD", default=None)

    if not all([username, email, password]):
        debug("❌ Skipping: Missing DJANGO_SU env variables.")
        return

    # 3. Create or update Superuser
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'is_staff': True, 'is_superuser': True, 'is_active': True}
    )

    if created:
        user.set_password(password)
        user.save()
        debug(f"✅ Created NEW superuser: {username}")
    else:
        # Sync flags and password if changed
        needs_save = False
        if not (user.is_staff and user.is_superuser and user.is_active):
            user.is_staff = user.is_superuser = user.is_active = True
            needs_save = True
        if not user.check_password(password):
            user.set_password(password)
            needs_save = True
        if needs_save:
            user.save()
            debug(f"✅ Updated existing superuser: {username}")

    # 4. Assign admin group to superuser only
    if not user.groups.filter(name='admin').exists():
        user.groups.add(admin_group)
        debug(f"✅ Superuser added to admin group")

    # 5. Ensure Customer profile exists for superuser
    Customer.objects.get_or_create(
        user=user,
        defaults={
            'username': user.username,
            'email': user.email,
            
        }
    )
    debug("✅ Admin-Customer profile sync complete.")

@receiver(post_delete)
def delete_images_on_model_delete(sender, instance, **kwargs):
    """
    Safely deletes Cloudinary files and ImageField files when a model instance is deleted.
    Handles:
      - CloudinaryField (with destroy)
      - ImageField (including CloudinaryStorage)
      - Windows path normalization
      - Missing files / HTTP errors
      - Skips during migrations or loaddata
    """
    # Skip during migrations or fixtures
    if 'migrate' in sys.argv or 'loaddata' in sys.argv:
        return

    for field in sender._meta.get_fields():
        # ------------------------------
        # 1) Handle CloudinaryField explicitly
        # ------------------------------
        if isinstance(field, CloudinaryField):
            file_field = getattr(instance, field.name, None)
            if file_field and getattr(file_field, 'public_id', None):
                try:
                    destroy(file_field.public_id, invalidate=True)
                    print(f"✅ Deleted Cloudinary file: {file_field.public_id}")
                except Exception as e:
                    print(f"❌ Error deleting Cloudinary file {file_field.public_id}: {e}")

        # ------------------------------
        # 2) Handle normal ImageField
        # ------------------------------
        elif isinstance(field, ImageField):
            file_field = getattr(instance, field.name, None)
            try:
                if file_field and file_field.name:
                    # Normalize Windows paths
                    file_name = file_field.name.replace("\\", "/")

                    # Check existence safely
                    if hasattr(file_field.storage, 'exists'):
                        exists = False
                        try:
                            exists = file_field.storage.exists(file_name)
                        except Exception as e:
                            print(f"⚠️ Warning: could not check existence for {file_name}: {e}")

                        if exists:
                            try:
                                file_field.delete(save=False)
                                print(f"✅ Deleted ImageField file: {file_name}")
                            except Exception as e:
                                print(f"❌ Error deleting ImageField file {file_name}: {e}")
            except Exception as e:
                print(f"⚠️ Unexpected error handling field {field.name}: {e}")

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


