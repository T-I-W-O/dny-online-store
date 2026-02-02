import json
import random
import datetime
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.template.loader import render_to_string
from django.core.exceptions import ImproperlyConfigured
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
import json
from .models import Coupon
from smtplib import SMTPException
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, is_naive
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.forms import inlineformset_factory
from .models import Product, ProductImage, ProductSize, ProductColor, Color
from .forms import ProductEditForm, ProductImageEditForm
from .decorators import allowed_users
from .forms import *
from datetime import datetime  # preferred
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.db.models import Prefetch
from collections import defaultdict
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError

from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User # Assuming User model is from django.contrib.auth.models
from django.db.models import Sum
from django.db.models import Avg, Count, Case, When, Value, IntegerField, Q
from django.contrib.auth.models import Group, AnonymousUser
import string
from smtplib import SMTPException
from django.utils.timesince import timesince
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.models import User, Group, AnonymousUser
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.core.mail import send_mail, BadHeaderError, EmailMultiAlternatives
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.urls import reverse
from django.shortcuts import render
from django.utils import timezone
from .models import Activities, Customer, GuestCustomer, Coupon # Make sure to import Coupon
import json # You might need this for consistency, though not strictly for this view
from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal
import json
from .decorators import *
from .forms import *
from .models import * # Be specific here if possible, e.g., Comment, CommentVote, Customer, PasswordResetCode, etc.



from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from django.shortcuts import render
from .models import Visitor, Order, Customer, Notice, GuestCustomer
from django.contrib.auth.models import Group


from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.models import Group
from .models import Order, Visitor, Customer, Notice
from .decorators import allowed_users  # adjust if needed

def get_week_range(year, week):
    """Returns the start (Monday) and end (next Monday) of the ISO week."""
    start_of_week = datetime.strptime(f'{year}-W{week}-1', "%G-W%V-%u")  # Monday
    start_of_week = timezone.make_aware(start_of_week)
    end_of_week = start_of_week + timedelta(days=7)  # Includes Sunday
    return start_of_week, end_of_week

@allowed_users(allowed_roles=['admin'])
def shop(request):
    # Parse selected week from GET param or use current week
    week_param = request.GET.get('week')  # Format: '2025-W29'
    today = timezone.now()

    if week_param:
        year, week = map(int, week_param.split('-W'))
    else:
        year, week = today.isocalendar()[0], today.isocalendar()[1]

    # Week range for selected/current week
    week_start, week_end = get_week_range(year, week)

    # Current week range (based on today)
    current_year, current_week = today.isocalendar()[0], today.isocalendar()[1]
    current_start, current_end = get_week_range(current_year, current_week)

    # Handle Week 1 case to avoid week=0
    if current_week == 1:
        last_year = current_year - 1
        last_week = datetime(last_year, 12, 28).isocalendar()[1]  # last ISO week of prev year
    else:
        last_year = current_year
        last_week = current_week - 1

    last_start, last_end = get_week_range(last_year, last_week)

    # ------------------ Data Calculations ------------------

    # Orders (Delivered this week vs last week)
    current_shipping_orders = (
        ShippingOrder.objects
        .filter(
            orders__status='Ongoing',
            created_at__range=(current_start, current_end)
        )
        .distinct()
        .count()
    )

    last_shipping_orders = (
        ShippingOrder.objects
        .filter(
            orders__status='Ongoing',
            created_at__range=(last_start, last_end)
        )
        .distinct()
        .count()
    )

    if last_shipping_orders == 0 and current_shipping_orders > 0:
        order_percent_change = 100
    elif last_shipping_orders == 0:
        order_percent_change = 0
    else:
        order_percent_change = round(
            ((current_shipping_orders - last_shipping_orders) / last_shipping_orders) * 100
        )

    # Visitors for selected/current week
    total_visits = Visitor.objects.filter(visited_at__range=(week_start, week_end)).count()
    unique_visitors = Visitor.objects.filter(visited_at__range=(week_start, week_end)).values('session_key').distinct().count()

    # Sales for selected/current week
    total_sales = Order.objects.filter(
        Q(status='Ongoing') | Q(status='Delivered'),
        date__range=(week_start, week_end)
    ).aggregate(
        Sum('total_price')
    )['total_price__sum'] or 0


    # Customers (New this week vs last week)
    current_customers = Customer.objects.filter(created_at__range=(current_start, current_end)).count()
    last_customers = Customer.objects.filter(created_at__range=(last_start, last_end)).count()

    if last_customers == 0 and current_customers > 0:
        customer_percent_change = 100
    elif last_customers == 0:
        customer_percent_change = 0
    else:
        customer_percent_change = round(((current_customers - last_customers) / last_customers) * 100)

    # ------------------ Slide ------------------

    slides = Slide.objects.all().order_by('-id')

    # ------------------ Context ------------------

    context = {
        'total_visits': total_visits,
        'unique_visitors': unique_visitors,
        'total_sales': total_sales,
        'slides': slides,
        'order_percent_change': order_percent_change,
        'this_week_order_count': current_shipping_orders,
        'selected_week': f"{year}-W{str(week).zfill(2)}",
        'new_customer_count': current_customers,
        'customer_percent_change': customer_percent_change,
    }

    return render(request, 'shop.html', context)


def custom_send_email(request):
    if request.method == 'POST':
        email = request.POST.get('to_email')

        if not email:
            return render(request, 'email_form.html', {'error': 'Email is required.'})

        try:
            user = User.objects.get(email=email)
            code = str(random.randint(10000, 99999))

            # Save reset code to DB
            PasswordResetCode.objects.create(user=user, code=code)

            context = {
                'user': user,
                'code': code
            }

            html_content = render_to_string('emails/password_reset.html', context)
            text_content = f"""
            Hello {user.username},

            You requested a password reset.
            Use this code to verify your identity: {code}

            If this wasn't you, please ignore this email.
            """

            email_obj = EmailMultiAlternatives(
                subject='Password Recovery Code',
                body=text_content,
                from_email='tiwoadex@gmail.com',
                to=[email]
            )
            email_obj.attach_alternative(html_content, "text/html")
            email_obj.send()

            return redirect('verify_code', pk=user.id)

        except User.DoesNotExist:
            return render(request, 'email_form.html', {'error': 'No user with that email address exists.'})
        except BadHeaderError:
            return render(request, 'email_form.html', {'error': 'Invalid header found.'})
        except SMTPException as e:
            return render(request, 'email_form.html', {'error': f'SMTP error: {str(e)}'})
        except ImproperlyConfigured as e:
            return render(request, 'email_form.html', {'error': f'Configuration error: {str(e)}'})
        except Exception as e:
            return render(request, 'email_form.html', {'error': f'Unexpected error: {str(e)}'})

    return render(request, 'email_form.html')


def verify_code(request, pk):  # Accept user ID from URL
    try:
        user = User.objects.get(pk=pk)  # Get user by primary key
    except User.DoesNotExist:
        return render(request, 'verify_code.html', {'error': 'User does not exist.'})

    if request.method == 'POST':
        entered_code = request.POST.get('code')

        try:
            reset_code = PasswordResetCode.objects.filter(user=user).latest('created_at')

            if reset_code.is_expired():
                return render(request, 'verify_code.html', {'error': 'Code expired. Please request a new one.', 'user': user})

            if entered_code == reset_code.code:
                return redirect('reset', pk=user.id, code=reset_code.code)

            else:
                return render(request, 'verify_code.html', {'error': 'Invalid code. Please try again.', 'user': user})

        except PasswordResetCode.DoesNotExist:
            return render(request, 'verify_code.html', {'error': 'No reset code found for this user.', 'user': user})

    # Initial GET request (page load)
    return render(request, 'verify_code.html', {'user': user})


def reset_password(request, pk, code):
    try:
        user = User.objects.get(pk=pk)
        reset_code = PasswordResetCode.objects.filter(user=user, code=code).latest('created_at')

        # Check expiration
        if reset_code.is_expired():
            return redirect('custom_send_email')  # Expired code

    except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
        return redirect('custom_send_email')  # Invalid user or code

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            return redirect('login')
    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': form})


def landingpage(request):
    return render(request, 'landingpage.html')


def product(request, pk):
    product = get_object_or_404(Product, id=pk)
    category = product.category
    goods = Product.objects.filter(category=category).exclude(id=pk)

    # Get customer if authenticated
    customer = None
    if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
        customer = Customer.objects.filter(user=request.user).first()

    # Guest customer from session
    session_key = request.session.session_key or request.session.save() or request.session.session_key
    guest_customer, _ = GuestCustomer.objects.get_or_create(session_key=session_key)

    # Get admin and customer groups
    admin_group = Group.objects.get(name="admin")
    customer_group = Group.objects.get(name="customer")

    # Annotate comments with group priority (admins = 0, others = 1), sort latest first
    comments = (
        Comment.objects.filter(product=product)
        .select_related('customer__user', 'guest_customer')
        .prefetch_related("replies")
        .annotate(
            group_order=Case(
                When(Q(customer__user__groups=admin_group), then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        )
        .order_by('group_order', '-time')
    )

    rating_data = product.comments.aggregate(
        average_rating=Avg('rating'),
        total_reviews=Count('rating')
    )
    average_rating = round(rating_data['average_rating'] or 0, 1)
    total_reviews = rating_data['total_reviews']


    # Product images
    main_images = product.images.filter(type='Main')
    other_images = product.images.filter(type='Other')
    product.main_image = main_images.first()

    # Size variants and color logic
    size_variants = ProductSize.objects.filter(product=product).prefetch_related('colors')
    color_variants = ProductColor.objects.filter(product=product).prefetch_related('colors').first()

    has_sizes = size_variants.exists()
    has_colors_only = not has_sizes and color_variants and color_variants.colors.exists()

    # Create size -> colors mapping
    size_color_map = {}
    for variant in size_variants:
        size_color_map[variant.size] = [color.color_name for color in variant.colors.all()]

    context = {
        'product': product,
        'main_images': main_images,
        'other_images': other_images,
        'comments': comments,
        'reply': Reply.objects.all(),  # optional: can be optimized
        'customer': customer,
        'guest_customer': guest_customer,
        'average_rating': average_rating,
        'total_reviews': total_reviews,
        'goods': goods,
        # new context for variant handling
        'has_sizes': has_sizes,
        'has_colors_only': has_colors_only,
        'size_color_map': size_color_map,
        'color_variants': color_variants,
    }

    return render(request, 'description.html', context)



def error(request):
    return render(request, 'error404.html')




def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Extract form data
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            number = form.cleaned_data['number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Create the user
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            user.save()

            # Assign the user to the 'customer' group
            try:
                customer_group = Group.objects.get(name='customer')
                customer_group.user_set.add(user)
            except Group.DoesNotExist:
                messages.error(request, "Customer group does not exist. Please contact the admin.")
                return render(request, 'register.html', {'form': form})

            # Create a Customer instance
            customer = Customer.objects.create(
                user=user,
                username=username,
                first_name=first_name,
                last_name=last_name,
                number=number,
                email=email,
            )
            customer.save()

            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
        else:
            # Form is invalid; display specific error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.groups.filter(name='customer').exists():
                auth_login(request, user)

                # Optional: log this login as a Visitor
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key

                try:
                    customer = Customer.objects.get(user=user)
                except Customer.DoesNotExist:
                    customer = None

                Visitor.objects.create(
                    session_key=session_key,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    customer=customer,
                    visited_at=now()
                )

                return redirect('home')

            elif user.groups.filter(name='admin').exists():
                auth_login(request, user)
                return redirect('shop')

            else:
                messages.error(request, "You do not have the appropriate permissions.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')

    return render(request, 'login.html')


def logoutpage(request):
    logout(request)
    return redirect('login')




def home(request):
    now = timezone.now()
    expired_coupons = Coupon.objects.filter(
            is_active=True,
            expires_at__isnull=False,
            expires_at__lt=now
        )
    expired_coupons.update(is_active=False)
    Notice.objects.filter(broadcast=True, expiry__lt=timezone.now()).delete()

    customer = None
    guest_customer = None

    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            customer = None
    else:
        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
        except GuestCustomer.DoesNotExist:
            guest_customer = None

    # === Visitor Tracking (record every visit) ===
    ip = request.META.get('REMOTE_ADDR')
    Visitor.objects.create(
        session_key=session_key,
        ip_address=ip,
        customer=customer,
        guest_customer=guest_customer
    )

    # === Product Filtering ===
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    filters = Q()

    if query:
        filters &= Q(name__icontains=query)

    if min_price and max_price:
        try:
            filters &= Q(price__gte=float(min_price), price__lte=float(max_price))
        except ValueError:
            pass

    products_list = Product.objects.filter(filters).order_by('-created_at').prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all()),
        Prefetch('size_variants', queryset=ProductSize.objects.prefetch_related('colors')),
        Prefetch('color_variants', queryset=ProductColor.objects.prefetch_related('colors')),
    )

    for product in products_list:
        product.main_image = product.images.filter(type='Main').first()
        if customer:
            activity = Activities.objects.filter(product=product, customer=customer).first()
            product.in_cart = activity.cart if activity else False
        elif guest_customer:
            activity = Activities.objects.filter(product=product, guest_customer=guest_customer).first()
            product.in_cart = activity.cart if activity else False
        else:
            product.in_cart = False

    paginator = Paginator(products_list, 15)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    expired_slides = Slide.objects.filter(created_at__lt=now - timedelta(hours=24))
    for slide in expired_slides:
        slide.delete() 
    # === Notices ===
    broadcast_notices = Notice.objects.filter(broadcast=True).order_by('-created_at')

    personal_notices = []
    if customer:
        personal_notices = Notice.objects.filter(
            customer=customer, broadcast=False, read=False
        ).order_by('-created_at')
    elif guest_customer:
        personal_notices = Notice.objects.filter(
            guest_customer=guest_customer, broadcast=False, read=False
        ).order_by('-created_at')

    context = {
        'products': products,
        'slides': Slide.objects.all(),
        'query': query,
        'min_price': min_price if min_price else 0,
        'max_price': max_price if max_price else 5000000,
        'customer': customer,
        'broadcast_notices': broadcast_notices,
        'personal_notices': personal_notices,
    }
    return render(request, 'home.html', context)

@csrf_exempt
def mark_notice_read(request, notice_id):
    if request.method == "POST":
        try:
            notice = Notice.objects.get(id=notice_id)
            notice.read = True
            notice.save()
            return HttpResponse("Marked as read", status=200)
        except Notice.DoesNotExist:
            return HttpResponse("Not found", status=404)
    return HttpResponse("Invalid request", status=400)


@csrf_exempt  # Optional if you're using the {% csrf_token %} and sending it via JS
def resend_otp_email(request, pk):
    if request.method == "POST":
        try:
            user = User.objects.get(pk=pk)
            to_email = user.email
            from_email = 'tiwoadex@gmail.com'
            subject = 'Password Recovery Code'
            code = str(random.randint(10000, 99999))

            # Save new code
            PasswordResetCode.objects.create(user=user, code=code)

            # Email context
            context = {'user': user, 'code': code}
            html_content = render_to_string('emails/password_reset.html', context)
            text_content = f"""Hello {user.username},\n\nUse this code to reset your password: {code}\n\nThanks."""

            # Send email
            email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()

            return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)





def order_confirm(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    customer = None
    guest_customer = None
    latest_transaction = None

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            latest_transaction = (
                Order.objects
                .filter(customer=customer, status='Ongoing')
                .order_by('-date', '-id')
                .values('transaction_id')
                .first()
            )
        except Customer.DoesNotExist:
            customer = None
    else:
        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            latest_transaction = (
                Order.objects
                .filter(guest_customer=guest_customer, status='Ongoing')
                .order_by('-date', '-id')
                .values('transaction_id')
                .first()
            )
        except GuestCustomer.DoesNotExist:
            guest_customer = None

    orders = []
    order_details = []
    shipping = None
    total_quantity = 0
    total_price = 0
    coupon_display = None
    
    subtotal = 0

    if latest_transaction:
        latest_transaction_id = latest_transaction['transaction_id']

        main_images = Prefetch(
            'product__images',
            queryset=ProductImage.objects.filter(type='Main'),
            to_attr='main_images'
        )

        order_filter = {'status': 'Ongoing', 'transaction_id': latest_transaction_id}
        if customer:
            order_filter['customer'] = customer
        elif guest_customer:
            order_filter['guest_customer'] = guest_customer

        orders = (
            Order.objects
            .filter(**order_filter)
            .select_related('product')
            .prefetch_related('details__size', 'details__colors', main_images)
        )

        order_details = (
            OrderDetail.objects
            .filter(order__in=orders)
            .prefetch_related('colors', 'size')
        )

        shipping_filter = {'orders__in': orders}
        if customer:
            shipping_filter['customer'] = customer
        elif guest_customer:
            shipping_filter['guest_customer'] = guest_customer

        shipping = (
            ShippingOrder.objects
            .filter(**shipping_filter)
            .distinct()
            .first()
        )

        total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
        total_price = orders.aggregate(total=Sum('total_price'))['total'] or 0

        # Default subtotal is total_price
        subtotal = total_price
        subtotal = total_price  # Default

        # Check coupon logic
        if shipping and shipping.coupon:
            print("Coupon exists.")

            coupon = shipping.coupon
            coupon_linked = False

            if customer and coupon.used_by_customer.filter(pk=customer.pk).exists():
                coupon_linked = True
                print("Coupon is linked to this authenticated user.")
            elif guest_customer and coupon.used_by_guest.filter(pk=guest_customer.pk).exists():
                coupon_linked = True
                print("Coupon is linked to this guest user.")
            else:
                print("Coupon isn't linked to this user.")

            if coupon_linked:
                if coupon.one_time_use:
                    print("Coupon is one-time use = True.")
                else:
                    print("Coupon is one-time use = False.")

                if coupon.is_percent:
                    discount_rate = coupon.amount / 100
                    try:
                        subtotal = total_price / (1 - discount_rate)
                        print(f"Calculated subtotal from {coupon.amount}% discount: {subtotal}")
                        coupon_display = f"-{coupon.amount}%"
                    except ZeroDivisionError:
                        subtotal = total_price  # fallback
                        print("Invalid discount rate of 100%. Subtotal fallback to total_price.")
                else:
                    subtotal = total_price + coupon.amount
                    coupon_display = f"-₦{coupon.amount}"
                    print(f"Calculated subtotal from ₦{coupon.amount} discount: {subtotal}")
        else:
            print("Coupon doesn't exist.")


    context = {
        'orders': orders,
        'order_details': order_details,
        'shipping': shipping,
        'customer': customer,
        'guest_customer': guest_customer,
        'total_quantity': total_quantity,
        'total_price': total_price,
        'coupon_display': coupon_display,
        'subtotal': subtotal,
    }

    return render(request, 'order_confirm.html', context)




def create_order_email(request):
    current_year = timezone.now().year
    customer = None
    guest_customer = None
    session_key = request.session.session_key

    # 🔍 Identify the user
    if request.user.is_authenticated:
        try:
            customer = request.user.customer
            latest_transaction = Order.objects.filter(
                customer=customer, status='Ongoing'
            ).order_by('-date', '-id').values('transaction_id').first()
        except Customer.DoesNotExist:
            latest_transaction = None
    else:
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            latest_transaction = Order.objects.filter(
                guest_customer=guest_customer, status='Ongoing'
            ).order_by('-date', '-id').values('transaction_id').first()
        except GuestCustomer.DoesNotExist:
            latest_transaction = None

    if not latest_transaction:
        print("❌ No ongoing order found.")
        return redirect('order_confirm')

    transaction_id = latest_transaction['transaction_id']

    # 🔄 Prefetch related items
    main_images = Prefetch(
        'product__images',
        queryset=ProductImage.objects.filter(type='Main'),
        to_attr='main_images'
    )

    orders = Order.objects.filter(
        transaction_id=transaction_id,
        status='Ongoing',
        customer=customer if customer else None,
        guest_customer=guest_customer if guest_customer else None
    ).select_related('product').prefetch_related('details__size', 'details__colors', main_images)

    order_details = OrderDetail.objects.filter(order__in=orders).prefetch_related('colors', 'size')

    # 📦 Get shipping info
    shipping = ShippingOrder.objects.filter(
        orders__in=orders,
        customer=customer if customer else None,
        guest_customer=guest_customer if guest_customer else None
    ).distinct().first()

    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
    total_price = orders.aggregate(total=Sum('total_price'))['total'] or 0

    to_email = shipping.email or (
        customer.user.email if customer else guest_customer.email
    ) or "noemail@unknown.com"

    username = customer.user.username if customer else guest_customer.first_name or "Guest"

    # 🎟 Handle applied coupon (if any)
    applied_coupon = request.session.get("applied_coupon")
    coupon_obj = None

    if applied_coupon:
        coupon_code = applied_coupon.get("code")

        try:
            coupon_obj = Coupon.objects.get(code__iexact=coupon_code, is_active=True)

            # 🧷 Link to customer or guest
            if customer and not coupon_obj.used_by_customer.filter(id=customer.id).exists():
                coupon_obj.used_by_customer.add(customer)
            elif guest_customer and not coupon_obj.used_by_guest.filter(id=guest_customer.id).exists():
                coupon_obj.used_by_guest.add(guest_customer)

            # ✅ Mark as used for one-time use coupons
            if not coupon_obj.one_time_use:
                coupon_obj.one_time_use = True
                coupon_obj.is_active = False
                coupon_obj.save()

            # 🔗 Link to shipping model
            if shipping:
                shipping.coupon = coupon_obj
                shipping.save()
                print(f"✅ Coupon linked to shipping order: {shipping.id}")

            print(f"✅ Coupon '{coupon_code}' marked and linked.")

        except Coupon.DoesNotExist:
            print("❌ Applied coupon does not exist.")

        # 🧹 Clear session
        if "applied_coupon" in request.session:
            del request.session["applied_coupon"]
            request.session.modified = True
            print("🧹 Coupon removed from session.")

    # ✉️ Send email
    subject = 'Your Order Confirmation'
    from_email = 'tiwoadex@gmail.com'

    context = {
        'customer': customer,
        'guest_customer': guest_customer,
        'orders': orders,
        'order_details': order_details,
        'shipping': shipping,
        'total_quantity': total_quantity,
        'total_price': total_price,
        'applied_coupon': applied_coupon,
        'now': current_year,
    }

    html_content = render_to_string('emails/order_summary.html', context)

    text_content = f"""
Hello {username},

Thank you for shopping with us!

Order Summary:
Total Items: {total_quantity}
Total Price: ₦{total_price}

Address:
{shipping.address}, {shipping.town}, {shipping.state}, {shipping.country}

Contact:
Email: {shipping.email}
WhatsApp: {shipping.whatsapp_number}

Regards,
Your Store Team
"""

    try:
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()
        print("✅ Email sent to", to_email)
    except BadHeaderError:
        print("❌ Bad header error.")
    except SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except ImproperlyConfigured as e:
        print(f"❌ Email config error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return redirect('order_confirm')



def category_view(request, category_name):
    customer = None
    if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            customer = None

    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    filters = Q(category__iexact=category_name)  # Main category filter

    if query:
        filters &= Q(name__icontains=query)

    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            filters &= Q(price__gte=min_price, price__lte=max_price)
        except ValueError:
            pass

    products_list = Product.objects.filter(filters).order_by('-created_at').prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all()),
        Prefetch('size_variants', queryset=ProductSize.objects.prefetch_related('colors')),
        Prefetch('color_variants', queryset=ProductColor.objects.prefetch_related('colors')),
    )

    for product in products_list:
        product.main_image = product.images.filter(type='Main').first()

        if customer:
            activity = Activities.objects.filter(product=product, customer=customer).first()
            product.in_cart = activity.cart if activity else False
        else:
            product.in_cart = False

    paginator = Paginator(products_list, 15)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    context = {
        'products': products,
        'category_name': category_name.title(),  # Optional, for template use
        'notices': Notice.objects.all(),
        'slides': Slide.objects.all(),
        'query': query,
        'min_price': min_price if min_price else 0,
        'max_price': max_price if max_price else 5000000,
        'customer': customer
    }
    return render(request, 'categories.html', context)



from .models import Notice  # Make sure this is imported
from django.db.models import Sum

from django.db.models import Sum
from .models import Customer, GuestCustomer, ShippingOrder, Notice

def profile(request):
    shipping_orders = []
    customer = None
    guest_customer = None
    notices = []

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            shipping_orders = ShippingOrder.objects.filter(customer=customer).order_by('-id')[:5]
            notices = Notice.objects.filter(customer=customer).order_by('-created_at')[:5]

            # ✅ Mark all unread notices as read for this customer
            Notice.objects.filter(customer=customer, read=False).update(read=True)

        except Customer.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            shipping_orders = ShippingOrder.objects.filter(guest_customer=guest_customer).order_by('-id')[:5]
            notices = Notice.objects.filter(guest_customer=guest_customer).order_by('-created_at')[:5]

            # ✅ Mark all unread notices as read for this guest
            Notice.objects.filter(guest_customer=guest_customer, read=False).update(read=True)

        except GuestCustomer.DoesNotExist:
            pass

    # Build order summary
    order_data = []
    for ship in shipping_orders:
        orders = ship.orders.all()
        total = orders.aggregate(total=Sum('total_price'))['total'] or 0
        date = orders.first().date if orders.exists() else None
        status = orders.first().status if orders.exists() else "Unknown"
        order_data.append({
            'transaction_id': orders.first().transaction_id if orders.exists() else "Unknown",
            'date': date,
            'total': total,
            'status': status,
            'shipping_id': ship.id,
        })

    latest_saved_shipping = ShippingOrder.objects.filter(
        customer=customer if customer else None,
        guest_customer=guest_customer if guest_customer else None,
        save_status='Save'
    ).order_by('-id').first()

    return render(request, 'profile.html', {
        'order_data': order_data,
        'customer': customer,
        'guest_customer': guest_customer,
        'latest_saved_shipping': latest_saved_shipping,
        'notices': notices,
    })



@csrf_exempt
def update_profile(request):
    if request.method == "POST":
        user = request.user
        customer = user.customer

        if request.content_type.startswith('multipart/form-data'):
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            number = request.POST.get('number', '').strip()
            image = request.FILES.get('image')

            # Check for duplicate email
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                return JsonResponse({"status": "error", "message": "This email is already in use."})

            # Update User model
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            # Update Customer model
            customer.first_name = first_name
            customer.last_name = last_name
            customer.email = email
            customer.number = number
            if image:
                customer.image = image
            customer.save()

            return JsonResponse({"status": "success"})

        return JsonResponse({"status": "error", "message": "Invalid request format."})


@login_required
@csrf_exempt
def verify_current_password(request):
    if request.method == "POST":
        data = json.loads(request.body)
        current_password = data.get('current_password')

        if not request.user.check_password(current_password):
            return JsonResponse({"status": "error", "message": "Current password is incorrect."})

        return JsonResponse({"status": "success"})

@csrf_exempt
@login_required
def change_password(request):
    if request.method == "POST":
        data = json.loads(request.body)
        new_password = data.get('new_password')

        user = request.user
        user.set_password(new_password)
        user.save()

        return JsonResponse({"status": "success"})









@csrf_exempt
def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
            size = data.get('size')
            color = data.get('color')
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid data format'}, status=400)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)

        # ✅ Use discounted price if available
        price = product.discounted_price if product.discounted_price is not None and product.discounted_price > 0 else product.price


        # ✅ LOGGED-IN USER
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)

                existing = Activities.objects.filter(
                    customer=customer,
                    product=product,
                    selected_size=size,
                    selected_color=color,
                    cart=True
                ).first()

                if existing:
                    if existing.quantity == quantity:
                        print("🟡 Already in cart (authenticated user)")
                        return JsonResponse({'success': False, 'message': 'Already in cart'})
                    else:
                        existing.quantity = quantity
                        existing.save()
                        print("🟢 Quantity updated (authenticated user)")
                        return JsonResponse({'success': True, 'message': 'Quantity updated'})
                else:
                    Activities.objects.create(
                        customer=customer,
                        product=product,
                        selected_size=size,
                        selected_color=color,
                        quantity=quantity,
                        price=price,
                        cart=True
                    )
                    print("🟢 New activity created (authenticated user)")
                    return JsonResponse({'success': True, 'message': 'Product added to cart'})

            except Customer.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Customer not found'}, status=404)

        # ✅ GUEST USER
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key

            # Get or create guest customer
            guest_customer, created = GuestCustomer.objects.get_or_create(session_key=session_key)
            if created:
                guest_customer.first_name = f"Guest-{session_key[:6]}"
                guest_customer.save()
                print(f"🆕 Created new GuestCustomer: {guest_customer}")

            # Check for existing matching entry
            existing = Activities.objects.filter(
                guest_customer=guest_customer,
                product=product,
                selected_size=size,
                selected_color=color,
                cart=True
            ).first()

            if existing:
                if existing.quantity == quantity:
                    print("🟡 Already in cart (guest user)")
                    return JsonResponse({'success': False, 'message': 'Already in cart'})
                else:
                    existing.quantity = quantity
                    existing.save()
                    print("🟢 Quantity updated (guest user)")
                    return JsonResponse({'success': True, 'message': 'Quantity updated'})
            else:
                Activities.objects.create(
                    guest_customer=guest_customer,
                    product=product,
                    selected_size=size,
                    selected_color=color,
                    quantity=quantity,
                    price=price,
                    cart=True
                )
                print("🟢 New activity created (guest user)")
                return JsonResponse({'success': True, 'message': 'Product added to cart'})

    # Optional: Clean session cart if any (even though you're no longer using it)
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
        print("🧹 Old session cart cleared")

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)







@csrf_exempt
def remove_from_cart(request, activity_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        activity = Activities.objects.get(id=activity_id)
    except Activities.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Activity not found'}, status=404)

    # Authenticated user
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            if activity.customer == customer:
                activity.delete()
                return JsonResponse({'success': True})
        except Customer.DoesNotExist:
            pass
    else:
        # Guest user
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({'success': False, 'message': 'No session'}, status=400)

        try:
            guest = GuestCustomer.objects.get(session_key=session_key)
            if activity.guest_customer == guest:
                activity.delete()
                return JsonResponse({'success': True})
        except GuestCustomer.DoesNotExist:
            pass

    return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)


def view_cart(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    raw_activities = []
    customer = None
    guest = None

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            raw_activities = Activities.objects.filter(customer=customer, cart=True).select_related('product')
        except Customer.DoesNotExist:
            pass
    else:
        try:
            guest = GuestCustomer.objects.get(session_key=session_key)
            raw_activities = Activities.objects.filter(guest_customer=guest, cart=True).select_related('product')
        except GuestCustomer.DoesNotExist:
            pass

    # Remove activities where product.limit == 0
    for act in raw_activities:
        if act.product and act.product.limit == 0:
            act.cart = False
            act.save()

    # Refresh filtered activities after cleanup
    if request.user.is_authenticated and customer:
        raw_activities = Activities.objects.filter(customer=customer, cart=True).select_related('product')
    elif guest:
        raw_activities = Activities.objects.filter(guest_customer=guest, cart=True).select_related('product')
    else:
        raw_activities = []

    # Enrich each activity for template display
    enriched_activities = []
    for act in raw_activities:
        enriched_activities.append({
            "id": act.id,
            "product": act.product,
            "quantity": act.quantity,
            "price": float(act.price),  # Ensure float for JSON serialization
            "total_price": float(act.quantity * act.price),
            "selected_color": act.selected_color,
            "selected_size": act.selected_size,
            "details": f"{act.quantity} - {act.selected_color or '-'}"
                       f"{(' size ' + act.selected_size) if act.selected_size else ''}"
        })

    # --- Coupon Logic Integration ---
    applied_coupon_data = request.session.get('applied_coupon', None)

    if applied_coupon_data:
        try:
            coupon = Coupon.objects.get(code__iexact=applied_coupon_data['code'], is_active=True)
            if coupon.expires_at and timezone.now() > coupon.expires_at:
                del request.session['applied_coupon']
                applied_coupon_data = None
            elif coupon.one_time_use and (coupon.used_by_customer.exists() or coupon.used_by_guest.exists()):
                del request.session['applied_coupon']
                applied_coupon_data = None
            else:
                applied_coupon_data = {
                    'code': coupon.code,
                    'amount': float(coupon.amount),
                    'is_percent': coupon.is_percent
                }
        except Coupon.DoesNotExist:
            request.session.pop('applied_coupon', None)
            applied_coupon_data = None
        except Exception as e:
            print(f"Error re-validating coupon: {e}")
            request.session.pop('applied_coupon', None)
            applied_coupon_data = None
    # --- End Coupon Logic ---

    return render(request, 'cart.html', {
        "activities": enriched_activities,
        "applied_coupon": json.dumps(applied_coupon_data) if applied_coupon_data else 'null'
    })



def generate_transaction_id():
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TXN-{random_part}"




def checkout(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    session_key = request.session.session_key or request.session.create()
    data = json.loads(request.body)
    activity_ids = data.get("activity_ids", [])

    if not activity_ids:
        return JsonResponse({"success": False, "message": "No items selected."})

    customer = None
    guest_customer = None

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            activities = Activities.objects.filter(id__in=activity_ids, customer=customer, cart=True)
        except Customer.DoesNotExist:
            activities = []
    else:
        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            activities = Activities.objects.filter(id__in=activity_ids, guest_customer=guest_customer, cart=True)
        except GuestCustomer.DoesNotExist:
            activities = []

    if not activities:
        return JsonResponse({"success": False, "message": "No valid cart items found."})

    # 🔍 STEP 1: Validate product quantity limits
    product_quantity_map = {}
    for act in activities:
        product = act.product
        if product:
            if product.id not in product_quantity_map:
                product_quantity_map[product.id] = {
                    'product': product,
                    'total_quantity': 0
                }
            product_quantity_map[product.id]['total_quantity'] += act.quantity

    for item in product_quantity_map.values():
        product = item['product']
        total_qty = item['total_quantity']
        if product.limit is not None and total_qty > product.limit:
            return JsonResponse({
                "success": False,
                "message": f"❌ '{product.name}' is limited to {product.limit} item(s). You selected {total_qty}. Please reduce the quantity."
            })

    # ✅ All product limits passed, proceed to order creation
    applied_coupon = request.session.get("applied_coupon")
    use_coupon = applied_coupon is not None
    txn_id = generate_transaction_id()

    for act in activities:
        item_price = Decimal(act.price) * Decimal(act.quantity)

        final_price = item_price
        if use_coupon:
            amount = Decimal(str(applied_coupon.get("amount", 0)))
            if applied_coupon.get("is_percent"):
                discount = (amount / Decimal('100')) * item_price
            else:
                discount = amount

            final_price = item_price - discount
            if final_price < 0:
                final_price = Decimal('0.00')

        order = Order.objects.create(
            product=act.product,
            customer=customer,
            guest_customer=guest_customer,
            total_price=final_price,
            quantity=act.quantity,
            status='Inactive',
            transaction_id=txn_id
        )

        order_detail = OrderDetail.objects.create(order=order)

        if act.selected_size:
            size_obj = ProductSize.objects.filter(size=act.selected_size, product=act.product).first()
            if size_obj:
                order_detail.size = size_obj
                order_detail.save()

        if act.selected_color:
            color_obj = Color.objects.filter(color_name=act.selected_color).first()
            if color_obj:
                order_detail.colors.add(color_obj)

    return JsonResponse({"success": True, "redirect_url": reverse('prepare_payment')})




def validate_shipping_order(request):
    """
    Handles AJAX validation for the shipping form.
    It returns a JSON response with 'success' or an 'error' message.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({'success': False, 'message': 'Session expired. Please refresh the page.'})

        # Get the latest order
        if request.user.is_authenticated:
            try:
                customer = Customer.objects.get(user=request.user)
                latest_order = Order.objects.filter(customer=customer, status="Inactive").order_by('-date', '-id').first()
            except Customer.DoesNotExist:
                latest_order = None
        else:
            try:
                guest_customer = GuestCustomer.objects.get(session_key=session_key)
                latest_order = Order.objects.filter(guest_customer=guest_customer, status="Inactive").order_by('-date', '-id').first()
            except GuestCustomer.DoesNotExist:
                latest_order = None

        if not latest_order:
            return JsonResponse({'success': False, 'message': 'No pending orders found to ship.'})

        transaction_id = latest_order.transaction_id
        orders = Order.objects.filter(transaction_id=transaction_id)

        # Validate stock limits
        product_totals = {}
        for order in orders:
            product = order.product
            if product:
                if product.id not in product_totals:
                    product_totals[product.id] = {'product': product, 'total_qty': 0}
                product_totals[product.id]['total_qty'] += order.quantity

        for item in product_totals.values():
            product = item['product']
            total_qty = item['total_qty']
            if product.limit is not None and total_qty > product.limit:
                error_message = f"⚠️ '{product.name}' is limited to {product.limit}. You selected {total_qty}. Please reduce the quantity."
                return JsonResponse({'success': False, 'message': error_message})

        # If all validations pass
        return JsonResponse({'success': True, 'message': 'Validation successful.'})
    
    # For non-AJAX requests or wrong method
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

def prepare_payment_ajax(request):
    """
    Handles an AJAX request to prepare payment details.
    This view returns a JSON response with the amount, reference, and email
    needed for the Paystack modal.
    """
    if request.method != 'GET' or not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'success': False, 'message': 'No active session.'})

    customer = None
    guest = None

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
            latest = Order.objects.filter(customer=customer, status='Inactive')\
                                 .order_by('-date', '-id').values('transaction_id').first()
        except Customer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Customer does not exist.'})
    else:
        guest = GuestCustomer.objects.filter(session_key=session_key).first()
        if not guest:
            return JsonResponse({'success': False, 'message': 'Guest session expired.'})
        
        latest = Order.objects.filter(guest_customer=guest, status='Inactive')\
                             .order_by('-date', '-id').values('transaction_id').first()

    if not latest:
        return JsonResponse({'success': False, 'message': 'No valid order found.'})

    transaction_id = latest['transaction_id']
    
    # Check if a transaction is already initiated with this transaction_id and is active.
    # This prevents creating multiple payments for the same order.
    # You might need to adjust this logic based on your `payment` model and status.
    
    orders = Order.objects.filter(transaction_id=transaction_id)
    total_amount = sum(order.total_price or 0 for order in orders)
    amount_in_kobo = int(total_amount * 100)

    # Email and reference from session
    shipping_data = request.session.get('shipping_data', {})
    email = shipping_data.get('email')
    
    if not email:
        email = customer.user.email if request.user.is_authenticated else guest.email

    reference = transaction_id

    # Make sure we have all the required data
    if not all([email, amount_in_kobo, reference]):
        return JsonResponse({'success': False, 'message': 'Missing payment information.'})

    return JsonResponse({
        'success': True,
        'email': email,
        'amount': amount_in_kobo,
        'reference': reference,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    })

def prepare_payment(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    customer = None
    guest_customer = None

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            latest_order = Order.objects.filter(customer=customer, status="Inactive").order_by('-date', '-id').first()
        except Customer.DoesNotExist:
            latest_order = None
    else:
        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            latest_order = Order.objects.filter(guest_customer=guest_customer, status="Inactive").order_by('-date', '-id').first()
        except GuestCustomer.DoesNotExist:
            latest_order = None

    orders = []
    total_quantity = 0
    total_price = 0
    transaction_id = None
    applied_coupon = request.session.get("applied_coupon")
    discount_amount = None
    discount_label = None

    if latest_order:
        transaction_id = latest_order.transaction_id
        orders = Order.objects.filter(transaction_id=transaction_id).prefetch_related('details__colors', 'details__size', 'product')
        total_quantity = sum(order.quantity for order in orders)
        total_price = sum(order.total_price for order in orders)

        # Coupon display logic
        if applied_coupon:
            amount = Decimal(str(applied_coupon.get("amount", 0)))
            is_percent = applied_coupon.get("is_percent", False)
            discount_label = f"-{int(amount)}%" if is_percent else f"-₦{int(amount):,}"
            discount_amount = discount_label

    latest_shipping = None
    if request.user.is_authenticated and customer:
        latest_shipping = ShippingOrder.objects.filter(customer=customer, save_status='Save').order_by('-created_at').first()
    elif guest_customer:
        latest_shipping = ShippingOrder.objects.filter(guest_customer=guest_customer, save_status='Save').order_by('-created_at').first()

    return render(request, 'order_summary.html', {
        'latest_order': latest_order,
        'orders': orders,
        'total_quantity': total_quantity,
        'total_price': total_price,
        'transaction_id': transaction_id,
        'latest_shipping': latest_shipping,
        "coupon_display": discount_label,
    })


def collect_shipping_info(request):
    """
    Handles AJAX request to save shipping info to the session.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Extract and sanitize form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address1 = request.POST.get('address1', '').strip()
        address2 = request.POST.get('address2', '').strip()
        country = request.POST.get('country')
        state = request.POST.get('state')
        town = request.POST.get('town')
        local_government = request.POST.get('local_government')
        email = request.POST.get('gmail')
        whatsapp_number = request.POST.get('whatsapp_number')
        order_note = request.POST.get('order_note', '').strip()
        delivery_type = request.POST.get('delivery_type', 'Delivery').capitalize()
        save_status = 'Save' if request.POST.get('save_info') else 'Unsave'

        # Basic form validation (can be more extensive)
        if not all([first_name, last_name, email, whatsapp_number, delivery_type]):
             return JsonResponse({'success': False, 'message': 'Please fill in all required fields.'})

        # Logic to save to session
        request.session['shipping_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'address': f"{address1} {address2}".strip(),
            'country': country,
            'state': state,
            'town': town,
            'local_government': local_government,
            'email': email,
            'whatsapp_number': whatsapp_number,
            'order_note': order_note,
            'mode': delivery_type,
            'save_status': save_status,
        }

        return JsonResponse({'success': True, 'message': 'Shipping information saved successfully.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)



def payment_success(request):
    # Get the shipping data from the session
    shipping_data = request.session.get('shipping_data')
    if not shipping_data:
        return redirect('view_cart')  # fallback if user somehow skipped form

    # Get the current session key
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Determine if user is logged in or a guest
    customer = None
    guest_customer = None

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            latest_order = Order.objects.filter(customer=customer, status="Inactive").order_by('-date', '-id').first()
        except Customer.DoesNotExist:
            latest_order = None
    else:
        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            latest_order = Order.objects.filter(guest_customer=guest_customer, status="Inactive").order_by('-date', '-id').first()
        except GuestCustomer.DoesNotExist:
            latest_order = None

    if not latest_order:
        return redirect('view_cart')

    # Gather all orders with the same transaction_id
    transaction_id = latest_order.transaction_id
    orders = Order.objects.filter(transaction_id=transaction_id)

    # Extract data from session
    address = shipping_data.get('address')
    country = shipping_data.get('country')
    state = shipping_data.get('state')
    town = shipping_data.get('town')
    local_government = shipping_data.get('local_government')
    email = shipping_data.get('email')
    whatsapp_number = shipping_data.get('whatsapp_number')
    order_note = shipping_data.get('order_note')
    mode = shipping_data.get('mode')
    save_status = shipping_data.get('save_status')
    first_name = shipping_data.get('first_name')
    last_name = shipping_data.get('last_name')
    # Unsave previous saved shipping address
    if save_status == 'Save':
        if customer:
            ShippingOrder.objects.filter(customer=customer, save_status='Save').update(save_status='Unsave')
        elif guest_customer:
            ShippingOrder.objects.filter(guest_customer=guest_customer, save_status='Save').update(save_status='Unsave')

    # Create the shipping order using data from session
    shipping_order = ShippingOrder.objects.create(
        customer=customer,
        guest_customer=guest_customer,
        address=address,
        country=country,
        state=state,
        town=town,
        local_government=local_government,
        email=email,
        whatsapp_number=whatsapp_number,
        deliverydate=now(),
        order_note=order_note,
        created_at=now(),
        mode=mode,
        save_status=save_status,
    )

    # Associate orders with the shipping order
    shipping_order.orders.set(orders)

    if not request.user.is_authenticated and guest_customer:
        guest_customer.first_name = first_name
        guest_customer.last_name = last_name
        guest_customer.email = email
        guest_customer.number = whatsapp_number
        guest_customer.save()

    notice_message = f"Your order #{transaction_id} has been successfully received! We'll send you an update when it ships."
    if customer:
        if customer.user.groups.filter(name='customer').exists():
            Notice.objects.create(
                notice=notice_message,
                customer=customer,
                url = reverse('order_detail', args=[shipping_order.id])
            )
    elif guest_customer:
        Notice.objects.create(
            notice=notice_message,
            guest_customer=guest_customer,
        )

    # ✅ Notify all admin users
    if customer:
        name = f"{customer.first_name} {customer.last_name}"
    elif guest_customer:
        name = f"{guest_customer.first_name} {guest_customer.last_name}"


    admin_message = f"{name} just ordered some product(s) (#{transaction_id})"
    try:
        admin_group = Group.objects.get(name='admin')
        admin_customers = Customer.objects.filter(user__in=admin_group.user_set.all())
        for admin_customer in admin_customers:
            Notice.objects.create(
                notice=admin_message,
                customer=admin_customer,
                from_customer=customer if customer else None,
                from_guest_customer=guest_customer if guest_customer else None,
                is_system = True,
                url = reverse('edit_order', args=[shipping_order.id])

            )
    except Group.DoesNotExist:
        pass

    orders.update(payment_status="Paid")
    # ✅ Update order status + product stock + clear activities
    orders.update(status="Ongoing")
    for order in orders:
        product = order.product
        quantity = order.quantity
        if product and quantity:
            product.limit = max(product.limit - quantity, 0)
            product.save()

        details = order.details.first()
        if details:
            size = details.size.size if details.size else None
            color_list = list(details.colors.all())

            # If there are colors, handle them
            if color_list:
                for color in color_list:
                    filters = {
                        'product': product,
                        'selected_size': size,
                        'selected_color': color.color_name,
                        'quantity': quantity,
                        'cart': True,
                    }
                    if customer:
                        filters['customer'] = customer
                    elif guest_customer:
                        filters['guest_customer'] = guest_customer

                    Activities.objects.filter(**filters).update(cart=False)

            else:
                # Handle products with no color
                filters = {
                    'product': product,
                    'selected_size': size,
                    'selected_color__isnull': True,
                    'quantity': quantity,
                    'cart': True,
                }
                if customer:
                    filters['customer'] = customer
                elif guest_customer:
                    filters['guest_customer'] = guest_customer

                Activities.objects.filter(**filters).update(cart=False)



    # Update guest customer info if not logged in


    
   

    # Clear the shipping info from session after use
    del request.session['shipping_data']
    return redirect('email')



@csrf_exempt
def create_comment_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'})

    gmail = data.get('gmail')
    comment = data.get('comment')
    rating = int(data.get('rating', 0))
    product_id = data.get('product_id')

    if not comment or rating <= 0 or not product_id:
        return JsonResponse({'success': False, 'message': 'Missing fields'})

    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        customer = get_object_or_404(Customer, user=request.user)
        new_comment = Comment.objects.create(
            customer=customer, product=product, comment=comment, rating=rating
        )
        commenter_name = f"{customer.first_name} {customer.last_name}"
        from_customer = customer
        from_guest = None
    else:
        session_key = request.session.session_key or request.session.create()
        guest, _ = GuestCustomer.objects.get_or_create(session_key=session_key)
        guest.email = gmail
        guest.save()
        new_comment = Comment.objects.create(
            guest_customer=guest, product=product, comment=comment, rating=rating
        )
        commenter_name = guest.full_name() if hasattr(guest, 'full_name') else "Guest User"
        from_customer = None
        from_guest = guest

    url = reverse('product', args=[new_comment.product.id]) + f"#comment-{new_comment.id}"


    # ✅ Send notice to all admin customers
    admin_customers = Customer.objects.filter(user__is_staff=True)
    for admin in admin_customers:
        Notice.objects.create(
            notice=f"{commenter_name} just commented on {product.name}",
            customer=admin,
            from_customer=from_customer,
            from_guest_customer=from_guest,
            url=url
        )

    return JsonResponse({
        'success': True,
        'comment_id': new_comment.id,
        'email': gmail if not request.user.is_authenticated else customer.email,
        'comment': comment,
        'rating': rating,
    })




@csrf_exempt
def delete_comment(request):
    if request.method == "POST":
        comment_id = request.POST.get("comment_id")
        try:
            comment = Comment.objects.get(id=comment_id)

            # Check if the comment belongs to logged in customer or guest via session
            if request.user.is_authenticated:
                if hasattr(request.user, 'customer') and comment.customer == request.user.customer:
                    comment.delete()
                    return JsonResponse({"success": True})
                elif request.user.is_superuser:
                    comment.delete()
                    return JsonResponse({"success": True})
                else:
                    return JsonResponse({"success": False, "message": "Not authorized"})
            else:
                session_key = request.session.session_key
                if session_key and comment.guest_customer and comment.guest_customer.session_key == session_key:
                    comment.delete()
                    return JsonResponse({"success": True})
                return JsonResponse({"success": False, "message": "Not authorized"})
        except Comment.DoesNotExist:
            return JsonResponse({"success": False, "message": "Comment not found"})
    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def ajax_create_reply(request):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    # Ensure only admins can reply
    if not request.user.groups.filter(name="admin").exists():
        return JsonResponse({'success': False, 'message': 'Only admins can reply.'})

    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        reply_text = data.get('reply_text')

        if not comment_id or not reply_text:
            return JsonResponse({'success': False, 'message': 'Missing fields.'})

        comment = Comment.objects.get(id=comment_id)
        customer = Customer.objects.get(user=request.user)

        # Create the reply
        reply = Reply.objects.create(
            comment=comment,
            customer=customer,
            reply=reply_text,
            time=now(),
            replying_customer=comment.customer,
            replying_guest=comment.guest_customer
        )

        # Build the URL to the product and scroll to comment section
        product_id = comment.product.id  # assuming Comment has a FK to Product
        url = reverse('product', args=[product_id]) + f"#comment-{comment.id}"

        # Send notification to the original commenter
        notice_text = "Admin just replied your comment"
        Notice.objects.create(
            notice=notice_text,
            from_customer=customer,  # admin
            customer=comment.customer if comment.customer else None,
            guest_customer=comment.guest_customer if not comment.customer else None,
            url=url
        )

        return JsonResponse({
            'success': True,
            'reply_id': reply.id,
            'reply_text': reply.reply,
            'email': customer.user.email,
            'time': reply.time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Comment not found.'})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin customer profile not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})



@require_POST
def delete_reply(request):
    reply_id = request.POST.get('reply_id')
    try:
        reply = Reply.objects.get(id=reply_id)
        reply.delete()
        return JsonResponse({'success': True})
    except Reply.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Reply not found'})


@csrf_exempt
def update_shipping_address(request, id):
    if request.method == 'POST':
        try:
            shipping = ShippingOrder.objects.get(id=id)
            shipping.address = request.POST.get('address', shipping.address)
            shipping.state = request.POST.get('state', shipping.state)
            shipping.town = request.POST.get('town', shipping.town)
            shipping.local_government = request.POST.get('local_government', shipping.local_government)
            shipping.save()
            return JsonResponse({'success': True})
        except ShippingOrder.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Shipping address not found.'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def unsave_shipping_address(request, id):
    if request.method == 'POST':
        try:
            shipping = ShippingOrder.objects.get(id=id)
            shipping.save_status = 'Unsave'
            shipping.save()
            return JsonResponse({'success': True})
        except ShippingOrder.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Shipping address not found.'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})



def apply_coupon(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('coupon_code', '').strip()

        if not code:
            return JsonResponse({'success': False, 'message': 'Coupon code is required.'})

        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'This coupon is not correct.'})

        if coupon.expires_at and timezone.now() > coupon.expires_at:
            return JsonResponse({'success': False, 'message': 'This coupon has expired.'})

        # ✅ GLOBAL one-time use check: if it's used by *anyone* already
        if coupon.one_time_use and (
            coupon.used_by_customer.exists() or coupon.used_by_guest.exists()
        ):
            return JsonResponse({
                'success': False,
                'message': 'This coupon has already been used.'
            })

        # ✅ Save valid coupon in session
        request.session['applied_coupon'] = {
            'code': coupon.code,
            'amount': float(coupon.amount),
            'is_percent': coupon.is_percent
        }

        return JsonResponse({
            'success': True,
            'amount': float(coupon.amount),
            'is_percent': coupon.is_percent,
            'code': coupon.code
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@require_POST
def remove_coupon(request):
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
    return JsonResponse({'success': True})



def track_order(request):
    customer = None
    guest_customer = None
    session_key = request.session.session_key

    if request.user.is_authenticated:
        try:
            customer = request.user.customer
            shipping_orders = ShippingOrder.objects.filter(customer=customer).prefetch_related('orders')
        except Customer.DoesNotExist:
            shipping_orders = ShippingOrder.objects.none()
    else:
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            shipping_orders = ShippingOrder.objects.filter(guest_customer=guest_customer).prefetch_related('orders')
        except GuestCustomer.DoesNotExist:
            shipping_orders = ShippingOrder.objects.none()

    # ✅ Prepare order summary data
    order_data = []
    for shipping in shipping_orders:
        orders = shipping.orders.all()

        if not orders.exists():
            continue

        transaction_id = orders.first().transaction_id
        total = orders.aggregate(total=Sum('total_price'))['total'] or 0
        status = orders.first().status
        created_date = shipping.created_at

        order_data.append({
            'transaction_id': transaction_id,
            'date': created_date,
            'total': total,
            'status': status,
            'shipping_id': shipping.id,  # Optional: can be used for "View" links
        })

    context = {
        'order_data': order_data
    }

    return render(request, 'track_order.html', context)


def order_detail(request, shipping_id):
    shipping = get_object_or_404(
        ShippingOrder.objects.prefetch_related(
            'orders__product',
            'orders__details__size',
            'orders__details__colors'
        ), 
        id=shipping_id
    )

    orders = shipping.orders.all()
    subtotal = orders.aggregate(total=Sum('total_price'))['total'] or 0

    coupon = shipping.coupon
    discount = 0
    grand_total = subtotal

    if coupon:
        if coupon.is_percent:
            discount = (coupon.amount / 100) * subtotal
        else:
            discount = coupon.amount

        if discount > subtotal:
            discount = subtotal

        grand_total = subtotal - discount

    context = {
        'shipping': shipping,
        'orders': orders,
        'subtotal': int(subtotal),
        'discount': int(discount),
        'grand_total': int(grand_total),
        'coupon': coupon,
    }
    return render(request, 'order_details.html', context)



def notification(request):
    customer = None
    guest_customer = None
    notices = []

    # Determine who is viewing the page
    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            notices = Notice.objects.filter(customer=customer).order_by('-created_at')
            
            # Mark unread notifications as read
            Notice.objects.filter(customer=customer, read=False).update(read=True)

        except Customer.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        try:
            guest_customer = GuestCustomer.objects.get(session_key=session_key)
            notices = Notice.objects.filter(guest_customer=guest_customer).order_by('-created_at')
            
            # Mark unread notifications as read
            Notice.objects.filter(guest_customer=guest_customer, read=False).update(read=True)

        except GuestCustomer.DoesNotExist:
            pass

    return render(request, 'notification.html', {
        'notices': notices,
        'customer': customer,
        'guest_customer': guest_customer,
    })




@allowed_users(allowed_roles=['admin'])
def products(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday

    # -------- Weekly Filtered Orders (kept for other sections if needed) --------
    weekly_orders = Order.objects.filter(
        status__in=['Ongoing', 'Delivered'],
        date__gte=start_of_week
    )

    # -------- Pie Chart: Top 5 Most Plentiful Products (by limit) --------
    # Get products ordered by their 'limit' (stock) in descending order
    most_plentiful_products = Product.objects.all().order_by('-limit')[:5]
    pie_labels = [p.name for p in most_plentiful_products]
    pie_data = [p.limit for p in most_plentiful_products] # Use the 'limit' as data

    # -------- Bar Chart: Top 5 Most Populated Categories (by number of products) --------
    # Count products per category and order by the count
    most_populated_categories = (
        Product.objects
        .values('category') # Group by category
        .annotate(product_count=Count('id')) # Count products in each group
        .order_by('-product_count')[:5] # Get top 5 categories by product count
    )
    bar_labels = [item['category'] for item in most_populated_categories]
    bar_data = [item['product_count'] for item in most_populated_categories]

    # -------- Totals and Stock Status --------
    total_products = Product.objects.count()
    finished_products = Product.objects.filter(limit=0).count()
    low_stock_products = Product.objects.filter(limit__lte=5).exclude(limit=0).count()

    try:
        admin_group = Group.objects.get(name='admin')
        admin_users = admin_group.user_set.all()
        admin_customers = Customer.objects.filter(user__in=admin_users)

        admin_notices = Notice.objects.filter(
            customer__in=admin_customers
        ).order_by('-created_at')[:10]
    except Group.DoesNotExist:
        admin_notices = Notice.objects.none()

    # -------- Product Table Data (for inventory list - sorted by created_at) --------
    all_products_sorted = Product.objects.all().order_by('-created_at')

    product_data = []
    for product in all_products_sorted:
        orders = Order.objects.filter(
            product=product,
            status__in=['Ongoing', 'Delivered']
        )
        unit_sold = orders.aggregate(total=Sum('quantity'))['total'] or 0
        revenue = unit_sold * product.price

        # Stock status
        if product.limit == 0:
            status = 'Out'
        elif product.limit <= 5:
            status = 'Low'
        else:
            status = 'OK'

        product_data.append({
            'id': product.pk,
            'name': product.name,
            'limit': product.limit,
            'unit_sold': unit_sold,
            'revenue': revenue,
            'price':product.price,
            'status': status,
            'discounted_price': float(product.discounted_price) if product.discounted_price else None,
            'created_at': product.created_at.isoformat()
        })

    # -------- Context --------
    context = {
        'total_products': total_products,
        'finished_products': finished_products,
        'low_stock_products': low_stock_products,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'bar_labels': bar_labels,
        'bar_data': bar_data,
        'product_data': product_data,
        'admin_notices': admin_notices,
    }

    return render(request, 'product.html', context)



def customer(request):
    customer_count = Customer.objects.count()
    guest_customer_count = GuestCustomer.objects.count()
    pie_labels = []
    pie_data = []

    bar_labels = []
    bar_data = []

    # Pie Chart - Registered Customers
    customer_chart_data = []
    for customer in Customer.objects.all():
        orders = Order.objects.filter(customer=customer, status__in=['Ongoing', 'Delivered'])
        total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
        if total_spent > 0:
            customer_chart_data.append((f'{customer.first_name} {customer.last_name}', total_spent))

    customer_chart_data.sort(key=lambda x: x[1], reverse=True)

    for name, spent in customer_chart_data[:5]:
        pie_labels.append(name)
        pie_data.append(float(spent))

    # Bar Chart - Guest Customers
    guest_chart_data = []
    for guest in GuestCustomer.objects.all():
        orders = Order.objects.filter(guest_customer=guest, status__in=['Ongoing', 'Delivered'])
        total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
        if total_spent > 0:
            guest_chart_data.append((f'{guest.first_name or "Guest"} {guest.last_name or ""}', total_spent))

    guest_chart_data.sort(key=lambda x: x[1], reverse=True)

    for name, spent in guest_chart_data[:5]:
        bar_labels.append(name)
        bar_data.append(float(spent))

    return render(request, 'customer.html', {
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'bar_labels': bar_labels,
        'bar_data': bar_data,
        'customer_count': customer_count,
        'guest_customer_count': guest_customer_count,
    })


# This is a new helper function that we'll use for the API endpoint
def get_customer_data_json(request):
    data = []

    # Registered Customers
    for customer in Customer.objects.all():
        orders = Order.objects.filter(customer=customer, status__in=['Ongoing', 'Delivered'])
        total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
        order_count = orders.count()

        data.append({
            'id': customer.id, # We need the ID for the URL
            'name': f'{customer.first_name} {customer.last_name}',
            'first_name': customer.first_name, # Added for search
            'last_name': customer.last_name, # Added for search
            'email': customer.email,
            'phone': customer.number,
            'orders': order_count,
            'total_spent': float(total_spent), # Convert Decimal to float for JSON
            'status': 'Customer',
            'type': 'customer' # A new field to easily identify the type
        })

    # Guest Customers
    for guest in GuestCustomer.objects.all():
        orders = Order.objects.filter(guest_customer=guest, status__in=['Ongoing', 'Delivered'])
        total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
        order_count = orders.count()
        
        # We need the ID for the URL. Use a distinct key to avoid conflicts.
        data.append({
            'id': guest.id, 
            'name': f'{guest.first_name or "Guest"} {guest.last_name or ""}',
            'first_name': guest.first_name, # Added for search
            'last_name': guest.last_name, # Added for search
            'email': guest.email or '',
            'phone': guest.number or '',
            'orders': order_count,
            'total_spent': float(total_spent), # Convert Decimal to float for JSON
            'status': 'Guest',
            'type': 'guest' # A new field to easily identify the type
        })

    # Sort data list by order count (descending)
    data.sort(key=lambda x: x['orders'], reverse=True)

    return JsonResponse({'customers': data})




def tests(request):
    # Get admin users and their notices

    return render(request, 'test.html')





@allowed_users(allowed_roles=['admin'])
def admin_notice(request):
    customer = request.user.customer
    Notice.objects.filter(broadcast=True, expiry__lt=timezone.now()).delete()

    # Retrieve general notices (broadcast=True)
    general_notifications = Notice.objects.filter(broadcast=True).order_by('-created_at')

    # Retrieve all other notices (broadcast=False)
    normal_notifications = Notice.objects.filter(broadcast=False,customer=customer).order_by('-created_at')

    context = {
        'general_notifications': general_notifications,
        'normal_notifications': normal_notifications,
    }
    return render(request, 'admin-notice.html',context)


@require_POST
@csrf_exempt  # Only use this for testing; better to use CSRF token in production
def mark_notice_as_read(request):
    import json
    data = json.loads(request.body)
    notice_id = data.get("notice_id")

    try:
        notice = Notice.objects.get(id=notice_id)
        notice.read = True
        notice.save()
        return JsonResponse({"success": True})
    except Notice.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notice not found"}, status=404)



@allowed_users(allowed_roles=['admin'])
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        image_form = ProductImageForm(request.POST, request.FILES)

        if all([product_form.is_valid(), image_form.is_valid()]):
            price = product_form.cleaned_data.get('price')
            discounted_price = product_form.cleaned_data.get('discounted_price')

            if discounted_price and discounted_price > price:
                messages.error(request, "Discounted price cannot be higher than actual price.")
                return redirect('add_product')

            product = product_form.save()

            # === Save Images ===
            images = [
                image_form.cleaned_data.get('image_1'),
                image_form.cleaned_data.get('image_2'),
                image_form.cleaned_data.get('image_3'),
                image_form.cleaned_data.get('image_4'),
                image_form.cleaned_data.get('image_5'),
            ]
            main_index = int(image_form.cleaned_data['main_image'])

            for i, image in enumerate(images):
                if image:
                    image_type = 'Main' if i == main_index else 'Other'
                    ProductImage.objects.create(product=product, image=image, type=image_type)

            # === Handle General Product Colors ===
            general_color_names = request.POST.getlist('general_colors[]')
            general_color_names = [c.strip() for c in general_color_names if c.strip()]
            has_general_colors = bool(general_color_names)

            # === Handle Dynamic Sizes and Colors ===
            sizes = {}
            for key in request.POST:
                if key.startswith('sizes['):
                    parts = key.replace('sizes[', '').replace(']', '').split('[')
                    if len(parts) == 2:
                        idx, field = parts
                        sizes.setdefault(idx, {'size': '', 'colors': []})
                        if field == 'name':
                            sizes[idx]['size'] = request.POST[key]
                    elif len(parts) == 3:
                        idx, _, _ = parts
                        color_values = request.POST.getlist(key)
                        sizes.setdefault(idx, {'size': '', 'colors': []})
                        sizes[idx]['colors'].extend(color_values)

            # === Custom Validation: Disallow size-only entries (no color)
            cleaned_sizes = []
            size_only_errors = False

            for item in sizes.values():
                size = item['size'].strip()
                colors = [c.strip() for c in item['colors'] if c.strip()]

                if size and not colors:
                    size_only_errors = True
                elif size and colors:
                    cleaned_sizes.append({'size': size, 'colors': colors})

            if size_only_errors:
                messages.error(request, "You can't add only size. Please specify at least one color for each size.")
                return redirect('add_product')

            has_size_colors = bool(cleaned_sizes)

            # === Final Validation: Don't allow both size+colors AND general colors
            if has_general_colors and has_size_colors:
                messages.error(request, "You cannot fill both 'Product Color' and 'Size + Color'. Please choose only one.")
                return redirect('add_product')

            # === Save General Product Colors
            if has_general_colors:
                color_objs = []
                for color_name in general_color_names:
                    color, _ = Color.objects.get_or_create(color_name=color_name)
                    color_objs.append(color)
                product_color = ProductColor.objects.create(product=product)
                product_color.colors.set(color_objs)

            # === Save Size + Colors
            if has_size_colors:
                for item in cleaned_sizes:
                    size_obj = ProductSize.objects.create(product=product, size=item['size'])
                    color_objs = []
                    for color_name in item['colors']:
                        color, _ = Color.objects.get_or_create(color_name=color_name)
                        color_objs.append(color)
                    size_obj.colors.set(color_objs)

            
            return redirect('admin-products')

        else:
            messages.error(request, "Please fix the form errors.")

    else:
        product_form = ProductForm()
        image_form = ProductImageForm()

    return render(request, 'add-product.html', {
        'product_form': product_form,
        'image_form': image_form,
        'categories': Product.CATEGORY_CHOICES,
    })




@allowed_users(allowed_roles=['admin'])
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, f"Product '{product.name}' has been deleted successfully.")
    return redirect('admin-products')  # Replace with your actual product list URL name




logger = logging.getLogger(__name__)

MAX_IMAGES_PER_PRODUCT = 5

def get_or_create_color_case_insensitive(color_name):
    color_qs = Color.objects.filter(color_name__iexact=color_name)
    if color_qs.exists():
        return color_qs.first()
    return Color.objects.create(color_name=color_name)

@allowed_users(allowed_roles=['admin'])
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    ProductImageFormSet = inlineformset_factory(
        Product,
        ProductImage,
        form=ProductImageEditForm,
        extra=0,
        can_delete=True,
        min_num=0,
        max_num=MAX_IMAGES_PER_PRODUCT
    )

    if request.method == 'POST':
        product_form = ProductEditForm(request.POST, request.FILES, instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES, instance=product)

        overall_valid = product_form.is_valid() and image_formset.is_valid()

        # Validate images: at least one, and only one 'Main'
        if overall_valid:
            cleaned_data_list = image_formset.cleaned_data
            main_image_count = 0
            active_forms = [data for data in cleaned_data_list if not data.get('DELETE')]

            if not active_forms:
                image_formset._non_form_errors = image_formset.non_form_errors() + [
                    "A product must have at least one image."
                ]
                overall_valid = False
            else:
                for data in active_forms:
                    if data.get('type') == 'Main':
                        main_image_count += 1

                if main_image_count > 1:
                    image_formset._non_form_errors = image_formset.non_form_errors() + [
                        "A product cannot have two main images. Please select only one 'Main' image."
                    ]
                    overall_valid = False

        try:
            product_variations_data = json.loads(request.POST.get('product_variations_json', '{}'))
        except json.JSONDecodeError:
            messages.error(request, "Invalid data submitted for product variations.")
            overall_valid = False
            product_variations_data = {}

        if overall_valid:
            try:
                with transaction.atomic():
                    # Save product and images
                    product_form.save()
                    image_formset.save()

                    submitted_product_size_ids = set()
                    submitted_colors_for_each_size = {}

                    # --- Handle Sizes and Associated Colors ---
                    for size_data in product_variations_data.get('sizes', []):
                        size_value = size_data.get('value')
                        size_id = size_data.get('id')

                        if size_id == 'new':
                            current_product_size = ProductSize.objects.create(product=product, size=size_value)
                        else:
                            current_product_size = get_object_or_404(ProductSize, id=size_id, product=product)
                            current_product_size.size = size_value
                            current_product_size.save()

                        submitted_product_size_ids.add(current_product_size.id)
                        submitted_colors_for_each_size[current_product_size.id] = set()

                        for color_data in size_data.get('colors', []):
                            color_name = color_data.get('name')
                            color_id = color_data.get('id')

                            if color_id == 'new':
                                color_obj = get_or_create_color_case_insensitive(color_name)
                            else:
                                color_obj = get_object_or_404(Color, id=color_id)
                                if color_obj.color_name != color_name:
                                    color_obj.color_name = color_name
                                    color_obj.save()

                            current_product_size.colors.add(color_obj)
                            submitted_colors_for_each_size[current_product_size.id].add(color_obj.id)

                    # --- Remove Unsubmitted Sizes ---
                    original_product_sizes_qs = ProductSize.objects.filter(product=product)
                    for ps in original_product_sizes_qs:
                        if ps.id not in submitted_product_size_ids:
                            ps.delete()

                    # --- Remove Unsubmitted Colors From Sizes ---
                    for ps in ProductSize.objects.filter(product=product):
                        existing_color_ids = set(ps.colors.values_list('id', flat=True))
                        submitted_color_ids = submitted_colors_for_each_size.get(ps.id, set())
                        to_remove_ids = existing_color_ids - submitted_color_ids
                        for color_id in to_remove_ids:
                            ps.colors.remove(color_id)

                    # --- Handle General Product Colors ---
                    product_color_variant, _ = ProductColor.objects.get_or_create(product=product)
                    submitted_general_color_ids = set()

                    for color_data in product_variations_data.get('general_colors', []):
                        color_name = color_data.get('name')
                        color_id = color_data.get('id')

                        if color_id == 'new':
                            color_obj = get_or_create_color_case_insensitive(color_name)
                        else:
                            color_obj = get_object_or_404(Color, id=color_id)
                            if color_obj.color_name != color_name:
                                color_obj.color_name = color_name
                                color_obj.save()

                        product_color_variant.colors.add(color_obj)
                        submitted_general_color_ids.add(color_obj.id)

                    existing_general_color_ids = set(product_color_variant.colors.values_list('id', flat=True))
                    to_remove_general_ids = existing_general_color_ids - submitted_general_color_ids
                    for color_id in to_remove_general_ids:
                        product_color_variant.colors.remove(color_id)

                    
                    return redirect('admin-products')

            except Exception as e:
                logger.exception("Error updating product variations for product ID: %s", pk)
                messages.error(request, f"An error occurred while saving changes: {e}")
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        product_form = ProductEditForm(instance=product)
        image_formset = ProductImageFormSet(instance=product)

    context = {
        'product': product,
        'product_form': product_form,
        'image_formset': image_formset,
    }
    return render(request, 'edit_product.html', context)


@allowed_users(allowed_roles=['admin']) # Re-add if you have this
def test(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        errors = {}
        if not title:
            errors['title'] = 'Title is required.'
        if not description:
            errors['description'] = 'Description is required.'
        if not image:
            errors['image'] = 'Image is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        slide = Slide.objects.create(title=title, description=description, image=image)
        slide_data = {
            'id': slide.id,
            'title': slide.title,
            'description': slide.description,
            'image_url': slide.image.url,
        }
        return JsonResponse({'success': True, 'slide': slide_data})

    slides = Slide.objects.all().order_by('-id')  # or '-created_at' if you have a timestamp

    return render(request, 'shop.html',{'slides':slides})




@csrf_exempt  # Only if you're not sending CSRF token with DELETE — can be avoided with JS token
def delete_slide(request, slide_id):
    if request.method == 'POST':
        try:
            slide = Slide.objects.get(id=slide_id)
            slide.delete()
            return JsonResponse({'success': True})
        except Slide.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Slide not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@allowed_users(allowed_roles=['admin'])
def orders(request):
    # Get admin users and their notices
    admin_group = Group.objects.get(name='admin')
    admin_users = admin_group.user_set.all()
    admin_customers = Customer.objects.filter(user__in=admin_users)
    admin_notices = Notice.objects.filter(
        customer__in=admin_customers
    ).order_by('-created_at')[:10]

    # Fetch shipping orders
    shipping_orders = (
        ShippingOrder.objects
        .prefetch_related('orders__product', 'customer', 'guest_customer')
        .order_by('-created_at')
    )

    # Counts using distinct to avoid duplicates
    total_orders_count = shipping_orders.count()
    inactive_orders_count  = shipping_orders.filter(orders__status='Inactive').distinct().count()
    ongoing_orders_count   = shipping_orders.filter(orders__status='Ongoing').distinct().count()
    delivered_orders_count = shipping_orders.filter(orders__status='Delivered').distinct().count()
    
    valid_orders = Order.objects.filter(status__in=['Ongoing', 'Delivered'])

    # --- Pie Chart: Most Ordered Products ---
    product_orders = (
        valid_orders
        .values('product__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:5]
    )
    pie_labels = [p['product__name'] for p in product_orders]
    pie_data = [p['total_quantity'] for p in product_orders]

    # --- Bar Chart: Most Ordered Categories ---
    category_orders = (
        valid_orders
        .values('product__category')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:5]
    )
    bar_labels = [c['product__category'] for c in category_orders]
    bar_data = [c['total_quantity'] for c in category_orders]

    # Build shipping order data for the template
    shipping_order_data = []
    for so in shipping_orders:
        orders_qs = so.orders.all()

        if orders_qs.exists():
            first_order = orders_qs.first()
            transaction_id = first_order.transaction_id
            status = first_order.status
        else:
            transaction_id = ""
            status = "Failed"

        products_count = orders_qs.count()
        total_price = orders_qs.aggregate(total=Sum('total_price'))['total'] or 0
        total_quantity = orders_qs.aggregate(total=Sum('quantity'))['total'] or 0

        if so.customer:
            customer_name = f"{so.customer.first_name} {so.customer.last_name}"
        elif so.guest_customer:
            customer_name = f"{so.guest_customer.first_name} {so.guest_customer.last_name}"
        else:
            customer_name = "Unknown"

        shipping_order_data.append({
            'id': so.id,
            'transaction_id': transaction_id,
            'products_count': products_count,
            'total_price': float(total_price),
            'total_quantity': total_quantity,
            'customer_name': customer_name.strip(),
            'status': status,
        })

    # Final context
    context = {
        'total_orders': total_orders_count,
        'inactive_orders': inactive_orders_count,
        'ongoing_orders': ongoing_orders_count,
        'delivered_orders': delivered_orders_count,
        'shipping_order_data': json.dumps(shipping_order_data),
        'admin_notices': admin_notices,  # added to pass to template
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'bar_labels': bar_labels,
        'bar_data': bar_data,
    }

    return render(request, 'order.html', context)

@allowed_users(allowed_roles=['admin'])
def edit_order(request, shipping_id):
    shipping_order = get_object_or_404(ShippingOrder, id=shipping_id)

    # Determine if this is a customer or guest
    if shipping_order.customer:
        person = shipping_order.customer
        person_type = "customer"
    else:
        person = shipping_order.guest_customer
        person_type = "guest"

    orders = shipping_order.orders.select_related('product').all()

    product_data = []
    total_amount = 0  # Track total here

    for order in orders:
        details = OrderDetail.objects.filter(order=order).prefetch_related('colors')
        size_name = None
        colors_list = []

        for detail in details:
            if detail.size:
                size_name = detail.size.size
            colors_list.extend([color.color_name for color in detail.colors.all()])

        price = order.product.discounted_price or order.product.price
        total_amount += price * order.quantity  # accumulate

        product_data.append({
            "image": order.product.images.filter(type='Main').first().image.url if order.product.images.exists() else None,
            "name": order.product.name,
            "quantity": order.quantity,
            "price": price,
            "size": size_name,
            "colors": colors_list,
        })

    context = {
        "shipping_order": shipping_order,
        "person": person,
        "person_type": person_type,
        "orders": orders,
        "product_data": product_data,
        "total_amount": total_amount,
    }

    return render(request, 'edit_order.html', context)



@require_POST
@csrf_exempt
def update_order_status(request, shipping_id):
    try:
        shipping_order = get_object_or_404(ShippingOrder, id=shipping_id)

        # Get data from AJAX request
        status = request.POST.get("status")
        payment_status = request.POST.get("payment_status")
        inactive_reason = request.POST.get("inactive_reason", "")



        # Validation — If Delivered but not Paid
        if status == "Delivered" and payment_status != "Paid":
            return JsonResponse({
                "success": False,
                "error": "Delivered orders must be marked as Paid."
            })


        # Update all orders in this shipping order
        orders = shipping_order.orders.all()
        for order in orders:
            order.status = status
            order.payment_status = payment_status
            order.save()

                # Debug prints
        if status == "Inactive":
            request.session["inactive_reason"] = inactive_reason.strip() if inactive_reason.strip() else "No reason provided."
            rejection_email(request, shipping_order)  # call the email function

        elif status == "Delivered":
            delivery_email(request, shipping_order)

        return JsonResponse({
            "success": True,
            "message": "Order status updated successfully.",
            "status": status,
            "payment_status": payment_status
        })

    except ShippingOrder.DoesNotExist:
        return JsonResponse({"success": False, "error": "Shipping order not found."})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})

def rejection_email(request, shipping_order):
    """
    Sends a rejection email to the customer or guest associated with the shipping order.
    Reason is taken from request.session['inactive_reason'] if available.
    """
    reason = request.session.get("inactive_reason", "No reason provided.")

    # Identify customer or guest
    customer = shipping_order.customer
    guest_customer = shipping_order.guest_customer

    # Get email address
    to_email = shipping_order.email or (
        customer.email if customer else guest_customer.email
    ) or "noemail@unknown.com"

    # Name
    if customer:
        username = f"{customer.first_name} {customer.last_name}"
    elif guest_customer:
        username = f"{guest_customer.first_name or 'Guest'} {guest_customer.last_name or ''}"
    else:
        username = "Customer"

    # Get all orders in this shipping order
    orders = shipping_order.orders.all()

    # Context for HTML template
    context = {
        "username": username,
        "orders": orders,
        "shipping": shipping_order,
        "reason": reason,
        "now": timezone.now(),
    }

    # Render HTML template (create this in templates/emails/rejection_email.html)
    html_content = render_to_string("emails/rejection_email.html", context)

    # Plain text fallback
    text_content = f"""
Hello {username},

Thank you for shopping with us. Unfortunately, after reviewing your order(s), we are unable to process it at this time.

Reason for Rejection:
{reason}

We sincerely apologize for any inconvenience this may cause. If payment was processed, a full refund will be issued within [X business days] to your original payment method.

If you believe this decision was made in error or would like assistance placing a new order, please contact our customer support team:
📧 +234 703 057 2996
📞 dnyhairng@gmail.com

Thank you for your understanding.

Kind regards,
DNY
Customer Service Team
"""

    subject = f"Update on Your Order – {orders.first().transaction_id if orders.exists() else 'Order'}"
    from_email = "tiwoadex@gmail.com"

    try:
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()
        print(f"✅ Rejection email sent to {to_email}")
    except BadHeaderError:
        print("❌ Bad header error.")
    except SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except ImproperlyConfigured as e:
        print(f"❌ Email config error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        # ✅ Clear the inactive reason from session after sending email
    if "inactive_reason" in request.session:
        del request.session["inactive_reason"]
        request.session.modified = True


def delivery_email(request, shipping_order):
    """
    Sends delivery confirmation email to customer or guest.
    """
    # Identify customer or guest
    customer = shipping_order.customer
    guest_customer = shipping_order.guest_customer

    # Get email address
    to_email = shipping_order.email or (
        customer.email if customer else guest_customer.email
    ) or "noemail@unknown.com"

    # Name
    if customer:
        username = f"{customer.first_name} {customer.last_name}"
    elif guest_customer:
        username = f"{guest_customer.first_name or 'Guest'} {guest_customer.last_name or ''}"
    else:
        username = "Customer"

    # Get all orders in this shipping order
    orders = shipping_order.orders.all()
    # Calculate total quantity and total price
    total_quantity = sum(order.quantity for order in orders)
    total_price = sum(order.total_price for order in orders)

    applied_coupon = shipping_order.coupon if shipping_order.coupon else None


    # Context for HTML template
    context = {
        "username": username,
        "orders": orders,
        "shipping": shipping_order,
        "now": timezone.now(),
        "total_quantity": total_quantity,
        "total_price": total_price,
        "applied_coupon": applied_coupon,
    }

    # Render HTML template (create this in templates/emails/delivery_email.html)
    html_content = render_to_string("emails/delivery_email.html", context)

    # Plain text fallback
    text_content = f"""
Hello {username},

Good news — your order(s) {', '.join(o.transaction_id for o in orders)} has been marked as delivered to the address you provided.

Delivery Details:
Date: {timezone.now().date()}
Address: {shipping_order.address}

Your order summary is attached.

Thank you for shopping with us!

Kind regards,
DNY
Customer Service Team
"""

    subject = f"Your Order [{orders.first().transaction_id if orders.exists() else 'Order'}] Has Been Delivered"
    from_email = "tiwoadex@gmail.com"

    try:
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()
        print(f"✅ Delivery email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send delivery email: {e}")



def notification_list_view(request):
    # ✅ 1. Delete expired broadcast notifications
    Notice.objects.filter(broadcast=True, expiry__lt=timezone.now()).delete()

    # ✅ 2. Get only active broadcast notifications
    notifications = Notice.objects.filter(broadcast=True).order_by('-created_at')

    data = [
        {
            'id': n.id,
            'notice': n.notice,
            'expiry': n.expiry.strftime('%Y-%m-%d') if n.expiry else 'No Expiry'
        }
        for n in notifications
    ]

    return JsonResponse({'notifications': data})




@csrf_exempt
def create_notification_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    try:
        body = json.loads(request.body)
        notice_text = body.get('notice', '').strip()
        expiry_date = body.get('expiry', '').strip()

        # Check that both fields are provided
        if not notice_text:
            return JsonResponse({'error': 'Notice message is required.'}, status=400)
        if not expiry_date:
            return JsonResponse({'error': 'Expiration date is required.'}, status=400)

        # Parse and validate expiry date
        try:
            naive_expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            expiry = timezone.make_aware(naive_expiry)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        # Check if date is in the past
        if expiry < timezone.now():
            return JsonResponse({'error': 'You cannot choose a past expiration date.'}, status=400)

        # Create the broadcasted notice
        Notice.objects.create(
            notice=notice_text,
            broadcast=True,
            expiry=expiry
        )

        return JsonResponse({'message': 'Notification created successfully.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def delete_notification_view(request, notice_id):
    if request.method == 'DELETE':
        try:
            notice = Notice.objects.get(id=notice_id, broadcast=True)
            notice.delete()
            return JsonResponse({'message': 'Notification deleted successfully.'})
        except Notice.DoesNotExist:
            return JsonResponse({'error': 'Notification not found.'}, status=404)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)



from django.utils import timezone
from django.http import JsonResponse

def get_all_coupons(request):
    if request.method == "GET":
        now = timezone.now()

        # Deactivate expired coupons
        expired_coupons = Coupon.objects.filter(
            is_active=True,
            expires_at__isnull=False,
            expires_at__lt=now
        )
        expired_coupons.update(is_active=False)

        all_coupons = Coupon.objects.all().order_by('-id')

        data = []
        for coupon in all_coupons:
            is_expired = coupon.expires_at and coupon.expires_at < now
            used_by_display = None

            if coupon.one_time_use:
                # First check registered customers
                if coupon.used_by_customer.exists():
                    user = coupon.used_by_customer.first()
                    used_by_display = f"{user.first_name} {user.last_name} (Registered)"
                # Then check guest customers
                elif coupon.used_by_guest.exists():
                    guest = coupon.used_by_guest.first()
                    used_by_display = f"{guest.first_name or 'Guest'} {guest.last_name or ''} (Unregistered)"

            data.append({
                'id': coupon.id,
                'code': coupon.code,
                'amount': str(coupon.amount),
                'is_percent': coupon.is_percent,
                'expires_at': coupon.expires_at.strftime('%Y-%m-%d') if coupon.expires_at else None,
                'is_active': coupon.is_active,
                'is_expired': is_expired,
                'used_by_display': used_by_display
            })

        return JsonResponse({'coupons': data})




@csrf_exempt
def delete_coupon(request, coupon_id):
    if request.method == "DELETE":
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.delete()
            return JsonResponse({'success': True})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon not found'}, status=404)




@csrf_exempt
@require_POST
def create_coupon_ajax(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        name = data.get('name')
        percentage_discount = data.get('percentageDiscount')
        normal_price_discount = data.get('normalPriceDiscount')
        expiry_date = data.get('expiryDate')

        if not name:
            return JsonResponse({'success': False, 'error': 'Coupon name is required.'}, status=400)

        if percentage_discount and normal_price_discount:
            return JsonResponse({'success': False, 'error': 'Cannot use both discount types.'}, status=400)

        if not percentage_discount and not normal_price_discount:
            return JsonResponse({'success': False, 'error': 'One discount type is required.'}, status=400)

        # Validate expiry date
        aware_expiry = None
        if expiry_date:
            date_obj = parse_date(expiry_date)
            if not date_obj:
                return JsonResponse({'success': False, 'error': 'Invalid date format.'}, status=400)

            # Convert date to datetime at midnight
            expiry_datetime = datetime.combine(date_obj, datetime.min.time())

            # Make it timezone aware
            if is_naive(expiry_datetime):
                aware_expiry = make_aware(expiry_datetime)

            # Check for past date
            if aware_expiry < timezone.now():
                return JsonResponse({'success': False, 'error': 'Expiry date cannot be in the past.'}, status=400)

        is_percent = bool(percentage_discount)
        amount = percentage_discount if is_percent else normal_price_discount

        coupon = Coupon.objects.create(
            code=name,
            amount=amount,
            is_percent=is_percent,
            expires_at=aware_expiry
        )

        return JsonResponse({
            'success': True,
            'coupon': {
                'id': coupon.id,
                'code': coupon.code,
                'amount': str(coupon.amount),
                'is_percent': coupon.is_percent,
                'expires_at': coupon.expires_at.strftime('%Y-%m-%d') if coupon.expires_at else None
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def send_coupon_email(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email')
        coupon_code = data.get('coupon_code')

        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)

        if not coupon_code:
            return JsonResponse({'success': False, 'error': 'Coupon code is required.'}, status=400)

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon not found.'}, status=404)

        context = {
            'code': coupon.code,
            'amount': coupon.amount,
            'is_percent': coupon.is_percent,
            'expires_at': coupon.expires_at.strftime('%Y-%m-%d') if coupon.expires_at else 'No expiry'
        }

        html_content = render_to_string('emails/coupon_gift.html', context)
        text_content = f"""
        Hello,

        You've received a coupon: {coupon.code}
        Discount: {'%' if coupon.is_percent else '₦'}{coupon.amount}
        Expiry Date: {context['expires_at']}

        Enjoy your savings!
        """

        email_obj = EmailMultiAlternatives(
            subject='🎁 You Received a Coupon!',
            body=text_content,
            from_email='your@email.com',
            to=[email]
        )
        email_obj.attach_alternative(html_content, "text/html")
        email_obj.send()

        return JsonResponse({'success': True, 'message': 'Email sent!'})

    except BadHeaderError:
        return JsonResponse({'success': False, 'error': 'Invalid email header.'}, status=500)
    except SMTPException as e:
        return JsonResponse({'success': False, 'error': f'SMTP error: {str(e)}'}, status=500)
    except ImproperlyConfigured as e:
        return JsonResponse({'success': False, 'error': f'Email config error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'}, status=500)


from django.db.models import Sum, F, Count
from django.shortcuts import get_object_or_404, render
from .models import Customer, GuestCustomer, ShippingOrder

def customer_detail_view(request, type, id):
    if type == 'customer':
        person = get_object_or_404(Customer, id=id)
        shipping_orders = ShippingOrder.objects.filter(customer=person)
    elif type == 'guest':
        person = get_object_or_404(GuestCustomer, id=id)
        shipping_orders = ShippingOrder.objects.filter(guest_customer=person)
    else:
        return render(request, '404.html', status=404)

    # Aggregate data for each shipping order
    shipping_orders_data = []
    for s_order in shipping_orders:
        orders = s_order.orders.all()
        if orders.exists():
            shipping_orders_data.append({
                'id': s_order.id,
                'transaction_id': orders.first().transaction_id,  # pick any
                'item_count': orders.count(),
                'total_amount': orders.aggregate(total=Sum('total_price'))['total'],
                'total_quantity': orders.aggregate(total_qty=Sum('quantity'))['total_qty'],
                'order_date': s_order.created_at,
                'status': orders.first().status  # same for all orders in shipping
            })

    return render(request, 'customer_detail.html', {
        'person': person,
        'type': type.capitalize(),
        'shipping_orders': shipping_orders_data
    })

def fz(request):
    return render(request, 'fzmovies.html')

def wonder(request):
    return render(request, 'wonder.html')
