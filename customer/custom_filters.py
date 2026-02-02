from django import template
from django import template
from datetime import timedelta
register = template.Library()
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))  # Fix key mismatch (int vs str)

@register.filter
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except:
        return ''

@register.filter
def get_activity(activities, product_id):
    for act in activities:
        if act.product.id == product_id:
            return act
    return None


@register.filter
def dictkey(dictionary, key):
    return dictionary.get(key, [])

@register.filter
def format_date_range(start_date):
    end_date = start_date + timedelta(days=14)

    if start_date.year == end_date.year:
        if start_date.month == end_date.month:
            # Same month: repeat the month name on both
            return f"{start_date.strftime('%B %#d')} - {end_date.strftime('%B %#d, %Y')}"
        else:
            # Different months, same year
            return f"{start_date.strftime('%B %#d')} - {end_date.strftime('%B %#d, %Y')}"
    else:
        # Different year too
        return f"{start_date.strftime('%B %#d, %Y')} - {end_date.strftime('%B %#d, %Y')}"

@register.filter
def to(value):
    return range(value)


@register.filter
def get_main_image_url(images):
    main_image = images.filter(type='Main').first()
    if main_image and main_image.image:
        return main_image.image.url
    return ''  



@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)




@register.filter
def format_k(value):
    try:
        value = float(value)
        if value >= 10000:
            value_k = value / 1000
            return f"₦{int(value_k)}k" if value_k.is_integer() else f"₦{round(value_k, 1)}k"

        # For values < 10,000: comma format, no trailing .00
        if value.is_integer():
            return f"₦{int(value):,}"
        else:
            cleaned = str(round(value, 2)).rstrip('0').rstrip('.')
            parts = cleaned.split(".")
            parts[0] = f"{int(parts[0]):,}"
            return f"₦{'.'.join(parts)}" if len(parts) > 1 else f"₦{parts[0]}"
    except (ValueError, TypeError):
        return value


@register.filter
def unique(value):
    return list(set(value))



from django import template
import re


@register.filter
def bold_name(message):
    """
    Bolds the name at the beginning of the message.
    Works for formats like:
    - "Isaac Ashaka just ordered..."
    - "Isaac Ashaka replied to..."
    - "Isaac Ashaka canceled order #123"
    """
    # Define possible action keywords that follow the name
    action_keywords = ['just ordered', 'replied to', 'canceled order','just commented']

    for keyword in action_keywords:
        pattern = rf"^(.+?) {keyword}"
        match = re.match(pattern, message)
        if match:
            name = match.group(1)
            bolded_name = f"<b>{name}</b>"
            return message.replace(name, bolded_name, 1)

    # If no keyword match, return original
    return message

@register.filter
def startswith(value, arg):
    """
    Returns True if value starts with arg.
    Usage: {{ some_string|startswith:"The product" }}
    """
    if isinstance(value, str):
        return value.startswith(arg)
    return False

from django import template

@register.filter
def only_order_updates(notices):

    comment_keywords = ['just ordered']

    filtered = []
    for n in notices:
        if not isinstance(n.notice, str):
            continue

        message = n.notice

       
        contains_keyword = any(keyword in message for keyword in comment_keywords)

        if  contains_keyword:
            filtered.append(n)

    return filtered

@register.filter
def only_product_updates(notices):
    """
    Filters notices that either:
    - Start with 'The product'
    - Contain phrases like 'just commented'

    Usage: {% for notice in admin_notices|only_product_or_comments %}
    """
    # Define additional inclusion phrases
    comment_keywords = ['just commented']

    filtered = []
    for n in notices:
        if not isinstance(n.notice, str):
            continue

        message = n.notice

        starts_with_product = message.startswith("The product")
        contains_keyword = any(keyword in message for keyword in comment_keywords)

        if starts_with_product or contains_keyword:
            filtered.append(n)

    return filtered

@register.filter
def bold_product_name(value):
    """
    Bolds the product name in messages that start with 'The product'.
    It wraps the words after 'The product' and before ' is' or ' was' in <b> tags.
    """
    if not isinstance(value, str):
        return value

    if value.startswith("The product"):
        match = re.search(r"The product (.+?) (is|was|has|stock|got)", value)
        if match:
            product_name = match.group(1)
            bolded = f"<b>{product_name}</b>"
            return value.replace(product_name, bolded, 1)

    return value



@register.filter
def get_field(form, field_name): # Ensure this name is 'get_field'
    """
    Allows to get a form field by its name.
    Usage: {{ form|get_field:'field_name' }}
    """
    try:
        return form[field_name]
    except KeyError:
        return None