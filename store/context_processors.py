from django.conf import settings
from .models import Cart

def site_config(request):
    # Cart count for navbar badge
    cart_count = 0
    if request.session.session_key:
        cart = Cart.objects.filter(session_key=request.session.session_key).first()
        if cart:
            cart_count = cart.item_count
    return {
        'site':    settings.SITE_CONFIG,
        'payment': settings.PAYMENT_CONFIG,
        'cart_count': cart_count,
    }
