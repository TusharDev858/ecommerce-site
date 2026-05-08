import json
import stripe
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Product, Category, ContactMessage, Cart, CartItem, Order, OrderItem
from .forms import RegistrationForm, ContactForm, CheckoutForm, ProductForm, ProductImageFormSet


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


def calc_shipping(subtotal):
    cfg = settings.PAYMENT_CONFIG
    threshold = Decimal(str(cfg.get('FREE_SHIPPING_ABOVE', 150)))
    cost      = Decimal(str(cfg.get('SHIPPING_COST', 12)))
    return Decimal('0') if subtotal >= threshold else cost


def home(request):
    featured_id = getattr(settings, 'FEATURED_PRODUCT_ID', None)
    featured = None
    if featured_id:
        featured = Product.objects.filter(pk=featured_id, is_active=True).first()
    if not featured:
        featured = Product.objects.filter(is_featured=True, is_active=True).first()
    if not featured:
        featured = Product.objects.filter(is_active=True).first()

    categories    = Category.objects.all()
    category_slug = request.GET.get('category', '')
    search_query  = request.GET.get('q', '')
    sort          = request.GET.get('sort', '')

    products = Product.objects.filter(is_active=True)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(tagline__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(metal__icontains=search_query) |
            Q(stone__icontains=search_query)
        )
    if featured:
        products = products.exclude(pk=featured.pk)

    sort_map = {
        'price_asc':  'price',
        'price_desc': '-price',
        'newest':     '-created_at',
        'name':       'name',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True)[:4]

    contact_form = ContactForm()
    if request.method == 'POST' and 'contact_submit' in request.POST:
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            msg = contact_form.save()
            try:
                send_mail(
                    subject=f"Contact: {msg.subject}",
                    message=f"From: {msg.name} <{msg.email}>\n\n{msg.message}",
                    from_email=msg.email,
                    recipient_list=[settings.SITE_CONFIG['CONTACT_EMAIL']],
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, "Message sent! We'll get back to you soon.")
            return redirect('home')

    return render(request, 'store/home.html', {
        'featured':        featured,
        'products':        products,
        'new_arrivals':    new_arrivals,
        'categories':      categories,
        'active_category': category_slug,
        'search_query':    search_query,
        'active_sort':     sort,
        'contact_form':    contact_form,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(
        is_active=True, category=product.category
    ).exclude(pk=product.pk)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
    })


def cart_view(request):
    cart     = get_or_create_cart(request)
    items    = cart.cartitem_set.select_related('product').all()
    subtotal = cart.subtotal
    shipping = calc_shipping(subtotal)
    total    = subtotal + shipping
    return render(request, 'store/cart.html', {
        'cart': cart, 'items': items,
        'subtotal': subtotal, 'shipping': shipping, 'total': total,
    })


@require_POST
def cart_add(request, product_id):
    product  = get_object_or_404(Product, pk=product_id, is_active=True)
    cart     = get_or_create_cart(request)
    size     = request.POST.get('size', '').strip()
    quantity = int(request.POST.get('quantity', 1))
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, size=size,
        defaults={'quantity': quantity}
    )
    if not created:
        item.quantity += quantity
        item.save()
    messages.success(request, f'"{product.name}" added to your bag.')
    next_url = request.POST.get('next', '')
    return redirect(next_url if next_url else 'cart')


@require_POST
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    item.delete()
    messages.info(request, "Item removed from bag.")
    return redirect('cart')


@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    qty  = int(request.POST.get('quantity', 1))
    if qty < 1:
        item.delete()
    else:
        item.quantity = qty
        item.save()
    return redirect('cart')


def checkout(request):
    cart  = get_or_create_cart(request)
    items = cart.cartitem_set.select_related('product').all()
    if not items:
        messages.warning(request, "Your bag is empty.")
        return redirect('cart')
    subtotal = cart.subtotal
    shipping = calc_shipping(subtotal)
    total    = subtotal + shipping
    pcfg     = settings.PAYMENT_CONFIG
    initial  = {}
    if request.user.is_authenticated:
        initial = {
            'full_name': request.user.get_full_name() or request.user.username,
            'email':     request.user.email,
        }
    form = CheckoutForm(request.POST or None, payment_config=pcfg, initial=initial)
    if request.method == 'POST' and form.is_valid():
        method = form.cleaned_data['payment_method']
        if method == 'stripe':
            return _handle_stripe(request, form, cart, items, subtotal, shipping, total)
        else:
            order = _save_order(request, form, cart, items, subtotal, shipping, total, method)
            return redirect('order_confirm', pk=order.pk)
    return render(request, 'store/checkout.html', {
        'form': form, 'items': items,
        'subtotal': subtotal, 'shipping': shipping, 'total': total,
        'pcfg': pcfg,
        'stripe_public_key': pcfg.get('STRIPE_PUBLIC_KEY', ''),
        'paypal_client_id':  pcfg.get('PAYPAL_CLIENT_ID', ''),
        'paypal_sandbox':    pcfg.get('PAYPAL_SANDBOX', True),
    })


def _save_order(request, form, cart, items, subtotal, shipping, total, method, payment_id=''):
    order = form.save(commit=False)
    order.user           = request.user if request.user.is_authenticated else None
    order.subtotal       = subtotal
    order.shipping_cost  = shipping
    order.total          = total
    order.payment_method = method
    order.payment_id     = payment_id
    order.is_paid        = method not in ('cod', 'bank')
    order.status         = 'confirmed' if order.is_paid else 'pending'
    order.save()
    for ci in items:
        OrderItem.objects.create(
            order=order, product=ci.product,
            product_name=ci.product.name, size=ci.size,
            quantity=ci.quantity, unit_price=ci.product.price,
        )
        ci.product.stock = max(0, ci.product.stock - ci.quantity)
        ci.product.save()
    cart.cartitem_set.all().delete()
    return order


def _handle_stripe(request, form, cart, items, subtotal, shipping, total, _=None):
    pcfg = settings.PAYMENT_CONFIG
    stripe.api_key = pcfg.get('STRIPE_SECRET_KEY', '')
    token = request.POST.get('stripeToken')
    if not token:
        messages.error(request, "Payment token missing. Please try again.")
        return redirect('checkout')
    try:
        charge = stripe.Charge.create(
            amount=int(total * 100),
            currency=pcfg.get('STRIPE_CURRENCY', 'usd'),
            source=token,
            description=f"Order for {form.cleaned_data['email']}",
        )
        order = _save_order(request, form, cart, items, subtotal, shipping, total, 'stripe', charge.id)
        messages.success(request, "Payment successful! Order confirmed.")
        return redirect('order_confirm', pk=order.pk)
    except stripe.error.CardError as e:
        messages.error(request, f"Card declined: {e.user_message}")
        return redirect('checkout')
    except Exception:
        messages.error(request, "Payment failed. Please try again.")
        return redirect('checkout')


def order_confirm(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'store/order_confirm.html', {'order': order})


@csrf_exempt
@require_POST
def paypal_capture(request):
    data      = json.loads(request.body)
    order_pk  = data.get('order_pk')
    paypal_id = data.get('paypal_order_id')
    try:
        order = Order.objects.get(pk=order_pk)
        order.payment_id = paypal_id
        order.is_paid    = True
        order.status     = 'confirmed'
        order.save()
        return JsonResponse({'status': 'ok'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name or user.username}!")
        return redirect('home')
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Welcome back!")
        return redirect(request.GET.get('next', 'home'))
    return render(request, 'store/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('home')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/order_history.html', {'orders': orders})


@superuser_required
def dashboard(request):
    all_products  = Product.objects.all()
    all_orders    = Order.objects.all()
    unread_msgs   = ContactMessage.objects.filter(is_read=False)
    recent_orders = all_orders[:10]
    return render(request, 'store/dashboard.html', {
        'products':        all_products,
        'recent_orders':   recent_orders,
        'unread_messages': unread_msgs,
        'total_products':  all_products.count(),
        'active_products': all_products.filter(is_active=True).count(),
        'total_orders':    all_orders.count(),
        'pending_orders':  all_orders.filter(status='pending').count(),
        'categories':      Category.objects.all(),
    })


@superuser_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.is_active       = True
            product.is_featured     = request.POST.get('is_featured') == 'on'
            product.is_new_arrival  = request.POST.get('is_new_arrival') == 'on'
            product.is_customizable = request.POST.get('is_customizable') == 'on'
            product.save()
            form.save_m2m()
            formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
            if formset.is_valid():
                for img_form in formset:
                    if img_form.cleaned_data.get('image'):
                        img_form.save()
            messages.success(request, f'"{product.name}" added and is now live on the store.')
            return redirect('dashboard')
        else:
            formset = ProductImageFormSet(request.POST, request.FILES)
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'Error — {field}: {e}')
    else:
        form    = ProductForm(initial={'is_active': True})
        formset = ProductImageFormSet()
    return render(request, 'store/product_form.html', {
        'form': form, 'formset': formset, 'action': 'Add Product',
    })


@superuser_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            edited = form.save(commit=False)
            edited.is_active       = request.POST.get('is_active') == 'on'
            edited.is_featured     = request.POST.get('is_featured') == 'on'
            edited.is_new_arrival  = request.POST.get('is_new_arrival') == 'on'
            edited.is_customizable = request.POST.get('is_customizable') == 'on'
            edited.save()
            form.save_m2m()
            formset = ProductImageFormSet(request.POST, request.FILES, instance=edited)
            if formset.is_valid():
                for img_form in formset:
                    if img_form.cleaned_data.get('DELETE') and img_form.instance.pk:
                        img_form.instance.delete()
                    elif img_form.cleaned_data.get('image'):
                        img_form.save()
            messages.success(request, f'"{edited.name}" updated successfully.')
            return redirect('dashboard')
        else:
            formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'Error — {field}: {e}')
    else:
        form    = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)
    return render(request, 'store/product_form.html', {
        'form': form, 'formset': formset, 'product': product, 'action': 'Edit Product',
    })


@superuser_required
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f'"{product.name}" {"activated" if product.is_active else "hidden"}.')
    return redirect('dashboard')


@superuser_required
def order_detail_admin(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {new_status}.")
    return render(request, 'store/order_detail_admin.html', {'order': order})


@superuser_required
def messages_view(request):
    msgs = ContactMessage.objects.all()
    msgs.filter(is_read=False).update(is_read=True)
    return render(request, 'store/messages.html', {'contact_messages': msgs})








# import json
# import stripe
# from decimal import Decimal

# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth import login, logout
# from django.contrib.auth.decorators import login_required, user_passes_test
# from django.contrib.auth.forms import AuthenticationForm
# from django.contrib import messages
# from django.conf import settings
# from django.core.mail import send_mail
# from django.db.models import Q
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST

# from .models import Product, Category, ContactMessage, Cart, CartItem, Order, OrderItem
# from .forms import RegistrationForm, ContactForm, CheckoutForm, ProductForm, ProductImageFormSet


# def superuser_required(view_func):
#     return user_passes_test(lambda u: u.is_superuser)(view_func)


# def get_or_create_cart(request):
#     if not request.session.session_key:
#         request.session.create()
#     cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
#     return cart


# def calc_shipping(subtotal):
#     cfg = settings.PAYMENT_CONFIG
#     threshold = Decimal(str(cfg.get('FREE_SHIPPING_ABOVE', 150)))
#     cost      = Decimal(str(cfg.get('SHIPPING_COST', 12)))
#     return Decimal('0') if subtotal >= threshold else cost


# def home(request):
#     featured_id = getattr(settings, 'FEATURED_PRODUCT_ID', None)
#     featured = None
#     if featured_id:
#         featured = Product.objects.filter(pk=featured_id, is_active=True).first()
#     if not featured:
#         featured = Product.objects.filter(is_featured=True, is_active=True).first()
#     if not featured:
#         featured = Product.objects.filter(is_active=True).first()

#     categories    = Category.objects.all()
#     category_slug = request.GET.get('category', '')
#     search_query  = request.GET.get('q', '')
#     sort          = request.GET.get('sort', '')

#     products = Product.objects.filter(is_active=True)
#     if category_slug:
#         products = products.filter(category__slug=category_slug)
#     if search_query:
#         products = products.filter(
#             Q(name__icontains=search_query) |
#             Q(tagline__icontains=search_query) |
#             Q(description__icontains=search_query) |
#             Q(metal__icontains=search_query) |
#             Q(stone__icontains=search_query)
#         )
#     if featured:
#         products = products.exclude(pk=featured.pk)

#     sort_map = {
#         'price_asc':  'price',
#         'price_desc': '-price',
#         'newest':     '-created_at',
#         'name':       'name',
#     }
#     products = products.order_by(sort_map.get(sort, '-created_at'))
#     new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True)[:4]

#     contact_form = ContactForm()
#     if request.method == 'POST' and 'contact_submit' in request.POST:
#         contact_form = ContactForm(request.POST)
#         if contact_form.is_valid():
#             msg = contact_form.save()
#             try:
#                 send_mail(
#                     subject=f"Contact: {msg.subject}",
#                     message=f"From: {msg.name} <{msg.email}>\n\n{msg.message}",
#                     from_email=msg.email,
#                     recipient_list=[settings.SITE_CONFIG['CONTACT_EMAIL']],
#                     fail_silently=True,
#                 )
#             except Exception:
#                 pass
#             messages.success(request, "Message sent! We'll get back to you soon.")
#             return redirect('home')

#     return render(request, 'store/home.html', {
#         'featured':        featured,
#         'products':        products,
#         'new_arrivals':    new_arrivals,
#         'categories':      categories,
#         'active_category': category_slug,
#         'search_query':    search_query,
#         'active_sort':     sort,
#         'contact_form':    contact_form,
#     })


# def product_detail(request, slug):
#     product = get_object_or_404(Product, slug=slug, is_active=True)
#     related = Product.objects.filter(
#         is_active=True, category=product.category
#     ).exclude(pk=product.pk)[:4]
#     return render(request, 'store/product_detail.html', {
#         'product': product,
#         'related': related,
#     })


# def cart_view(request):
#     cart     = get_or_create_cart(request)
#     items    = cart.cartitem_set.select_related('product').all()
#     subtotal = cart.subtotal
#     shipping = calc_shipping(subtotal)
#     total    = subtotal + shipping
#     return render(request, 'store/cart.html', {
#         'cart': cart, 'items': items,
#         'subtotal': subtotal, 'shipping': shipping, 'total': total,
#     })


# @require_POST
# def cart_add(request, product_id):
#     product  = get_object_or_404(Product, pk=product_id, is_active=True)
#     cart     = get_or_create_cart(request)
#     size     = request.POST.get('size', '').strip()
#     quantity = int(request.POST.get('quantity', 1))
#     item, created = CartItem.objects.get_or_create(
#         cart=cart, product=product, size=size,
#         defaults={'quantity': quantity}
#     )
#     if not created:
#         item.quantity += quantity
#         item.save()
#     messages.success(request, f'"{product.name}" added to your bag.')
#     next_url = request.POST.get('next', '')
#     return redirect(next_url if next_url else 'cart')


# @require_POST
# def cart_remove(request, item_id):
#     item = get_object_or_404(CartItem, pk=item_id)
#     item.delete()
#     messages.info(request, "Item removed from bag.")
#     return redirect('cart')


# @require_POST
# def cart_update(request, item_id):
#     item = get_object_or_404(CartItem, pk=item_id)
#     qty  = int(request.POST.get('quantity', 1))
#     if qty < 1:
#         item.delete()
#     else:
#         item.quantity = qty
#         item.save()
#     return redirect('cart')


# def checkout(request):
#     cart  = get_or_create_cart(request)
#     items = cart.cartitem_set.select_related('product').all()
#     if not items:
#         messages.warning(request, "Your bag is empty.")
#         return redirect('cart')
#     subtotal = cart.subtotal
#     shipping = calc_shipping(subtotal)
#     total    = subtotal + shipping
#     pcfg     = settings.PAYMENT_CONFIG
#     initial  = {}
#     if request.user.is_authenticated:
#         initial = {
#             'full_name': request.user.get_full_name() or request.user.username,
#             'email':     request.user.email,
#         }
#     form = CheckoutForm(request.POST or None, payment_config=pcfg, initial=initial)
#     if request.method == 'POST' and form.is_valid():
#         method = form.cleaned_data['payment_method']
#         if method == 'stripe':
#             return _handle_stripe(request, form, cart, items, subtotal, shipping, total)
#         else:
#             order = _save_order(request, form, cart, items, subtotal, shipping, total, method)
#             return redirect('order_confirm', pk=order.pk)
#     return render(request, 'store/checkout.html', {
#         'form': form, 'items': items,
#         'subtotal': subtotal, 'shipping': shipping, 'total': total,
#         'pcfg': pcfg,
#         'stripe_public_key': pcfg.get('STRIPE_PUBLIC_KEY', ''),
#         'paypal_client_id':  pcfg.get('PAYPAL_CLIENT_ID', ''),
#         'paypal_sandbox':    pcfg.get('PAYPAL_SANDBOX', True),
#     })


# def _save_order(request, form, cart, items, subtotal, shipping, total, method, payment_id=''):
#     order = form.save(commit=False)
#     order.user           = request.user if request.user.is_authenticated else None
#     order.subtotal       = subtotal
#     order.shipping_cost  = shipping
#     order.total          = total
#     order.payment_method = method
#     order.payment_id     = payment_id
#     order.is_paid        = method not in ('cod', 'bank')
#     order.status         = 'confirmed' if order.is_paid else 'pending'
#     order.save()
#     for ci in items:
#         OrderItem.objects.create(
#             order=order, product=ci.product,
#             product_name=ci.product.name, size=ci.size,
#             quantity=ci.quantity, unit_price=ci.product.price,
#         )
#         ci.product.stock = max(0, ci.product.stock - ci.quantity)
#         ci.product.save()
#     cart.cartitem_set.all().delete()
#     return order


# def _handle_stripe(request, form, cart, items, subtotal, shipping, total, _=None):
#     pcfg = settings.PAYMENT_CONFIG
#     stripe.api_key = pcfg.get('STRIPE_SECRET_KEY', '')
#     token = request.POST.get('stripeToken')
#     if not token:
#         messages.error(request, "Payment token missing. Please try again.")
#         return redirect('checkout')
#     try:
#         charge = stripe.Charge.create(
#             amount=int(total * 100),
#             currency=pcfg.get('STRIPE_CURRENCY', 'usd'),
#             source=token,
#             description=f"Order for {form.cleaned_data['email']}",
#         )
#         order = _save_order(request, form, cart, items, subtotal, shipping, total, 'stripe', charge.id)
#         messages.success(request, "Payment successful! Order confirmed.")
#         return redirect('order_confirm', pk=order.pk)
#     except stripe.error.CardError as e:
#         messages.error(request, f"Card declined: {e.user_message}")
#         return redirect('checkout')
#     except Exception:
#         messages.error(request, "Payment failed. Please try again.")
#         return redirect('checkout')


# def order_confirm(request, pk):
#     order = get_object_or_404(Order, pk=pk)
#     return render(request, 'store/order_confirm.html', {'order': order})


# @csrf_exempt
# @require_POST
# def paypal_capture(request):
#     data      = json.loads(request.body)
#     order_pk  = data.get('order_pk')
#     paypal_id = data.get('paypal_order_id')
#     try:
#         order = Order.objects.get(pk=order_pk)
#         order.payment_id = paypal_id
#         order.is_paid    = True
#         order.status     = 'confirmed'
#         order.save()
#         return JsonResponse({'status': 'ok'})
#     except Order.DoesNotExist:
#         return JsonResponse({'status': 'error'}, status=404)


# def register(request):
#     if request.user.is_authenticated:
#         return redirect('home')
#     form = RegistrationForm(request.POST or None)
#     if form.is_valid():
#         user = form.save()
#         login(request, user)
#         messages.success(request, f"Welcome, {user.first_name or user.username}!")
#         return redirect('home')
#     return render(request, 'store/register.html', {'form': form})


# def login_view(request):
#     if request.user.is_authenticated:
#         return redirect('home')
#     form = AuthenticationForm(request, data=request.POST or None)
#     if request.method == 'POST' and form.is_valid():
#         login(request, form.get_user())
#         messages.success(request, "Welcome back!")
#         return redirect(request.GET.get('next', 'home'))
#     return render(request, 'store/login.html', {'form': form})


# def logout_view(request):
#     logout(request)
#     messages.info(request, "You've been logged out.")
#     return redirect('home')


# @login_required
# def order_history(request):
#     orders = Order.objects.filter(user=request.user)
#     return render(request, 'store/order_history.html', {'orders': orders})


# @superuser_required
# def dashboard(request):
#     all_products  = Product.objects.all()
#     all_orders    = Order.objects.all()
#     unread_msgs   = ContactMessage.objects.filter(is_read=False)
#     recent_orders = all_orders[:10]
#     return render(request, 'store/dashboard.html', {
#         'products':        all_products,
#         'recent_orders':   recent_orders,
#         'unread_messages': unread_msgs,
#         'total_products':  all_products.count(),
#         'active_products': all_products.filter(is_active=True).count(),
#         'total_orders':    all_orders.count(),
#         'pending_orders':  all_orders.filter(status='pending').count(),
#         'categories':      Category.objects.all(),
#     })


# @superuser_required
# def product_add(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES)  # FIX: added request.FILES
#         if form.is_valid():
#             product = form.save(commit=False)
#             product.is_active = True  # FIX: always active when added from dashboard
#             product.save()
#             form.save_m2m()
#             formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
#             if formset.is_valid():
#                 formset.save()
#             messages.success(request, f'"{product.name}" added and is now live on the store.')
#             return redirect('dashboard')
#         else:
#             formset = ProductImageFormSet(request.POST, request.FILES)
#             for field, errs in form.errors.items():
#                 for e in errs:
#                     messages.error(request, f'Error in {field}: {e}')
#     else:
#         form    = ProductForm(initial={'is_active': True})
#         formset = ProductImageFormSet()
#     return render(request, 'store/product_form.html', {
#         'form': form, 'formset': formset, 'action': 'Add Product',
#     })


# @superuser_required
# def product_edit(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES, instance=product)  # FIX: added request.FILES
#         if form.is_valid():
#             form.save()
#             formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
#             if formset.is_valid():
#                 formset.save()
#             messages.success(request, f'"{product.name}" updated successfully.')
#             return redirect('dashboard')
#         else:
#             formset = ProductImageFormSet(request.POST, request.FILES, instance=product)
#             for field, errs in form.errors.items():
#                 for e in errs:
#                     messages.error(request, f'Error in {field}: {e}')
#     else:
#         form    = ProductForm(instance=product)
#         formset = ProductImageFormSet(instance=product)
#     return render(request, 'store/product_form.html', {
#         'form': form, 'formset': formset, 'product': product, 'action': 'Edit Product',
#     })


# @superuser_required
# def product_toggle(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     product.is_active = not product.is_active
#     product.save()
#     status = "activated" if product.is_active else "hidden"
#     messages.success(request, f'"{product.name}" {status}.')
#     return redirect('dashboard')


# @superuser_required
# def order_detail_admin(request, pk):
#     order = get_object_or_404(Order, pk=pk)
#     if request.method == 'POST':
#         new_status = request.POST.get('status')
#         if new_status in dict(Order.STATUS_CHOICES):
#             order.status = new_status
#             order.save()
#             messages.success(request, f"Order status updated to {new_status}.")
#     return render(request, 'store/order_detail_admin.html', {'order': order})


# @superuser_required
# def messages_view(request):
#     msgs = ContactMessage.objects.all()
#     msgs.filter(is_read=False).update(is_read=True)
#     return render(request, 'store/messages.html', {'contact_messages': msgs})
