from .models import *
from django.utils import timezone

def cart_count(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    total_items = 0

    if request.user.is_authenticated:
        try:
            customer = Customer.objects.get(user=request.user)
            total_items = Activities.objects.filter(customer=customer, cart=True).count()
        except Customer.DoesNotExist:
            pass
    else:
        try:
            guest = GuestCustomer.objects.get(session_key=session_key)
            total_items = Activities.objects.filter(guest_customer=guest, cart=True).count()
        except GuestCustomer.DoesNotExist:
            pass

    return {'cart_count': total_items}


def notice_context(request):
    customer = None
    guest_customer = None
    session_key = request.session.session_key

    if request.user.is_authenticated:
        customer = getattr(request.user, 'customer', None)
    elif session_key:
        guest_customer = GuestCustomer.objects.filter(session_key=session_key).first()

    notice = None
    unread_count = 0

    if customer:
        notices = Notice.objects.filter(customer=customer, read=False)
        notice = notices.first()
        unread_count = notices.count()
    elif guest_customer:
        notices = Notice.objects.filter(guest_customer=guest_customer, read=False)
        notice = notices.first()
        unread_count = notices.count()

    return {
        'active_notice': notice,
        'unread_notice_count': unread_count
    }



