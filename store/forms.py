from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, ProductImage, ContactMessage, Order


class RegistrationForm(UserCreationForm):
    email      = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=False)
    last_name  = forms.CharField(max_length=50, required=False)

    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class ContactForm(forms.ModelForm):
    class Meta:
        model  = ContactMessage
        fields = ('name', 'email', 'subject', 'message')


class CheckoutForm(forms.ModelForm):
    class Meta:
        model  = Order
        fields = [
            'full_name', 'email', 'phone',
            'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country',
            'gift_note', 'payment_method',
        ]
        widgets = {
            'gift_note':     forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional gift message'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc. (optional)'}),
        }

    def __init__(self, *args, payment_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        if payment_config:
            choices = []
            if payment_config.get('STRIPE_ENABLED'):
                choices.append(('stripe', '💳  Credit / Debit Card (Stripe)'))
            if payment_config.get('PAYPAL_ENABLED'):
                choices.append(('paypal', '🅿  PayPal'))
            if payment_config.get('COD_ENABLED'):
                choices.append(('cod', '💵  ' + payment_config.get('COD_LABEL', 'Cash on Delivery')))
            if payment_config.get('BANK_ENABLED'):
                choices.append(('bank', '🏦  Bank Transfer'))
            self.fields['payment_method'].choices = choices


class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = [
            'name', 'category', 'tagline', 'description',
            'price', 'compare_price', 'stock', 'sku',
            'metal', 'stone', 'stone_carat', 'weight_grams',
            'dimensions', 'sizes_available', 'hallmark',
            'is_customizable', 'is_featured', 'is_new_arrival', 'is_active',
        ]
        widgets = {
            'description':     forms.Textarea(attrs={'rows': 6}),
            'sizes_available': forms.TextInput(attrs={'placeholder': 'e.g. 5,6,7,8,9 or 45cm,50cm,55cm'}),
        }


class ProductImageForm(forms.ModelForm):
    """Custom image form — image is not required so empty slots are skipped."""
    image = forms.ImageField(required=False)

    class Meta:
        model  = ProductImage
        fields = ['image', 'alt_text', 'is_primary']


ProductImageFormSet = forms.inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=4,
    max_num=10,
    can_delete=True,
)





# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from .models import Product, ProductImage, ContactMessage, Order


# class RegistrationForm(UserCreationForm):
#     email      = forms.EmailField(required=True)
#     first_name = forms.CharField(max_length=50, required=False)
#     last_name  = forms.CharField(max_length=50, required=False)

#     class Meta:
#         model  = User
#         fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


# class ContactForm(forms.ModelForm):
#     class Meta:
#         model  = ContactMessage
#         fields = ('name', 'email', 'subject', 'message')


# class CheckoutForm(forms.ModelForm):
#     class Meta:
#         model  = Order
#         fields = [
#             'full_name', 'email', 'phone',
#             'address_line1', 'address_line2',
#             'city', 'state', 'postal_code', 'country',
#             'gift_note', 'payment_method',
#         ]
#         widgets = {
#             'gift_note':      forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional gift message to include in the package'}),
#             'address_line2':  forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc. (optional)'}),
#         }

#     def __init__(self, *args, payment_config=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         if payment_config:
#             choices = []
#             if payment_config.get('STRIPE_ENABLED'):
#                 choices.append(('stripe', '💳  Credit / Debit Card (Stripe)'))
#             if payment_config.get('PAYPAL_ENABLED'):
#                 choices.append(('paypal', '🅿  PayPal'))
#             if payment_config.get('COD_ENABLED'):
#                 choices.append(('cod', '💵  ' + payment_config.get('COD_LABEL', 'Cash on Delivery')))
#             if payment_config.get('BANK_ENABLED'):
#                 choices.append(('bank', '🏦  Bank Transfer'))
#             self.fields['payment_method'].choices = choices


# class ProductForm(forms.ModelForm):
#     class Meta:
#         model  = Product
#         fields = [
#             'name', 'category', 'tagline', 'description',
#             'price', 'compare_price', 'stock', 'sku',
#             'metal', 'stone', 'stone_carat', 'weight_grams',
#             'dimensions', 'sizes_available', 'hallmark',
#             'is_customizable', 'is_featured', 'is_new_arrival', 'is_active',
#         ]
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 6}),
#             'sizes_available': forms.TextInput(attrs={'placeholder': 'e.g. 5,6,7,8,9 or 45cm,50cm,55cm'}),
#         }


# ProductImageFormSet = forms.inlineformset_factory(
#     Product, ProductImage,
#     fields=['image', 'alt_text', 'is_primary', 'order'],
#     extra=4, max_num=10, can_delete=True,
# )
