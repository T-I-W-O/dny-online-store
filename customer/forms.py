import re
from django.contrib.auth.models import User
from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(render_value=True),
        help_text="Password must be at least 8 characters long and contain at least one digit."
    )

    class Meta:
        model = Customer
        fields = ['username', 'first_name', 'last_name', 'number', 'email','password']

    def clean_password(self):
        password = self.cleaned_data.get('password')

        # Check if password meets the criteria
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long and must contain at least one digit.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")

        return password
    
    def clean_username(self):
        username = self.cleaned_data['username']

        existing_user = User.objects.filter(username=username).exists()
        if existing_user:
            self.add_error('username', "A user with that name already exists")
        return username
    
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email




class CustomEmailForm(forms.Form):
    to_email = forms.EmailField(label='Your Email')





class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')

        # Check if password meets the criteria
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password')
        password2 = cleaned_data.get('confirm_password')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data



ALLOWED_TYPES = ['image/jpeg', 'image/png']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'limit', 'discounted_price', 'description', 'category']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['discounted_price'].required = False


class ProductImageForm(forms.Form):
    image_1 = forms.ImageField(required=True)
    image_2 = forms.ImageField(required=False)
    image_3 = forms.ImageField(required=False)
    image_4 = forms.ImageField(required=False)
    image_5 = forms.ImageField(required=False)
    main_image = forms.ChoiceField(choices=[(str(i), f'Image {i+1}') for i in range(5)], required=True)

    def clean(self):
        cleaned_data = super().clean()
        images = [
            cleaned_data.get('image_1'),
            cleaned_data.get('image_2'),
            cleaned_data.get('image_3'),
            cleaned_data.get('image_4'),
            cleaned_data.get('image_5'),
        ]
        valid_images = [img for img in images if img]

        if not valid_images:
            raise ValidationError("At least one image is required.")

        for img in valid_images:
            if img and img.content_type not in ALLOWED_TYPES:
                raise ValidationError("Only JPG, JPEG, or PNG files are allowed.")

        main_index = int(cleaned_data.get('main_image'))
        if main_index >= len(valid_images):
            raise ValidationError("Main image selection is invalid.")

        return cleaned_data


class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'limit', 'discounted_price', 'description', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discounted_price = cleaned_data.get('discounted_price')

        # Check discounted_price against price
        if discounted_price is not None and discounted_price > price:
            self.add_error('discounted_price', "Discounted price cannot be higher than the actual price.")

        return cleaned_data

class ProductImageEditForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.image:
            self.fields['image'].required = False




class ProductSizeEditForm(forms.ModelForm):
    # Note: 'colors' (M2M field) is NOT included here because it's handled manually
    # in the view using dynamic inputs and not via a standard form field.
    class Meta:
        model = ProductSize
        fields = ['size']

class ProductColorEditForm(forms.ModelForm):
    # Note: 'colors' (M2M field) is NOT included here because it's handled manually
    # in the view using dynamic inputs and not via a standard form field.
    class Meta:
        model = ProductColor
        fields = [] # No direct fields, as it holds M2M for Colors, which are managed separately


# Create formsets with extra=0 to only show existing forms
ProductSizeFormSet = inlineformset_factory(
    Product,
    ProductSize,
    form=ProductSizeEditForm,
    extra=0, # No empty forms by default
    can_delete=True,
    min_num=0,
    validate_min=False
)

# For ProductColor (general variants):
# We want only ONE ProductColor instance linked to the Product.
# If one exists, it should be displayed. If not, one should be implicitly created/managed.
# Using max_num=1 here helps enforce that.
# We will ensure that if no ProductColor instance exists for the product, one is created.
ProductColorFormSet = inlineformset_factory(
    Product,
    ProductColor,
    form=ProductColorEditForm,
    extra=0, # No empty forms by default on load
    can_delete=False, # No delete button for the 'variant' box itself
    max_num=1, # Only one ProductColor variant allowed per product
    validate_max=True # Enforce max_num
)
