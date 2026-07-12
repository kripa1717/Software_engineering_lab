from datetime import timedelta
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.utils import timezone

from .models import User, InventoryItem, Vendor, Order, Alert, Forecast, Report, StockLog
from .forms import (
    RegisterForm, InventoryItemForm, StockUpdateForm,
    VendorForm, OrderForm, ReportFilterForm,
)
from .decorators import admin_required, staff_or_admin_required


# ---------- R-1 / R-2: Registration & Login ----------

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data['role']
            user.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'inventory/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid email/username or password.')
    return render(request, 'inventory/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- Dashboard ----------

@login_required
def dashboard_view(request):
    _check_low_stock_and_expiry_alerts()
    items = InventoryItem.objects.all()
    unread_alerts = Alert.objects.filter(IsRead=False).order_by('-createdAt')[:5]
    context = {
        'items': items,
        'unread_alerts': unread_alerts,
        'is_admin': request.user.role == 'Admin',
    }
    return render(request, 'inventory/dashboard.html', context)


def _check_low_stock_and_expiry_alerts():
    """R-6 & R-7: run threshold/expiry checks and generate alerts as needed."""
    for item in InventoryItem.objects.all():
        if item.quantity <= 0:
            if not Alert.objects.filter(itemId=item, type='Empty', IsRead=False).exists():
                Alert.generate(item, 'Empty', f"{item.name} is out of stock.")
        elif item.checkThreshold():
            if not Alert.objects.filter(itemId=item, type='Lowstock', IsRead=False).exists():
                Alert.generate(item, 'Lowstock', f"{item.name} is below minimum threshold.")

        if item.isexpiringsoon():
            if not Alert.objects.filter(itemId=item, type='Expiry', IsRead=False).exists():
                Alert.generate(item, 'Expiry', f"{item.name} is expiring soon ({item.expirydate}).")


# ---------- R-3 / R-4: Inventory Items ----------

@staff_or_admin_required
def inventory_list_view(request):
    items = InventoryItem.objects.all()
    return render(request, 'inventory/inventory_list.html', {'items': items})


@admin_required
def add_item_view(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item added successfully.')
            return redirect('inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'inventory/inventory_list.html', {'form': form, 'items': InventoryItem.objects.all()})


@staff_or_admin_required
def update_stock_view(request, item_id):
    item = get_object_or_404(InventoryItem, itemID=item_id)
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            change_type = form.cleaned_data['changeType']
            qty = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']

            if change_type == 'Restock':
                item.updateQuantity(item.quantity + qty)
            else:
                item.updateQuantity(max(item.quantity - qty, 0))

            StockLog.objects.create(
                itemId=item, userId=request.user,
                changeType=change_type, quantityChanged=qty, reason=reason,
            )
            messages.success(request, f'{item.name} stock updated.')
            return redirect('inventory_list')
    else:
        form = StockUpdateForm()
    return render(request, 'inventory/inventory_list.html', {'update_form': form, 'update_item': item, 'items': InventoryItem.objects.all()})


# ---------- R-6 / R-7: Alerts ----------

@staff_or_admin_required
def alert_list_view(request):
    alerts = Alert.objects.all().order_by('-createdAt')
    return render(request, 'inventory/alert_list.html', {'alerts': alerts})


@staff_or_admin_required
def mark_alert_read_view(request, alert_id):
    alert = get_object_or_404(Alert, alertId=alert_id)
    alert.MarkasRead()
    return redirect('alert_list')


# ---------- R-8 / R-9: Forecast ----------

@admin_required
def forecast_view(request):
    period_start = timezone.now().date()
    period_end = period_start + timedelta(days=7)

    forecast_data = {}
    for item in InventoryItem.objects.all():
        usage_total = StockLog.objects.filter(
            itemId=item, changeType='Usage',
            changedAt__gte=timezone.now() - timedelta(days=30),
        ).aggregate(total=Sum('quantityChanged'))['total'] or 0
        forecast_data[str(item.itemID)] = round(usage_total / 4, 2)  # simple weekly average

    forecast = Forecast.objects.create(
        periodstart=period_start, periodend=period_end, forecastData=forecast_data,
    )
    suggestions = forecast.generateReorderSuggestions()
    return render(request, 'inventory/forecast.html', {'forecast': forecast, 'suggestions': suggestions})


# ---------- R-10 / R-11: Vendors ----------

@admin_required
def vendor_list_view(request):
    vendors = Vendor.objects.all()
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor added successfully.')
            return redirect('vendor_list')
    else:
        form = VendorForm()
    return render(request, 'inventory/vendor_list.html', {'vendors': vendors, 'form': form})


# ---------- R-12: Orders ----------

@admin_required
def order_list_view(request):
    orders = Order.objects.all().order_by('-orderDate')
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.placeOrder()
            messages.success(request, 'Order placed successfully.')
            return redirect('order_list')
    else:
        form = OrderForm()
    return render(request, 'inventory/order_list.html', {'orders': orders, 'form': form})


@admin_required
def confirm_delivery_view(request, order_id):
    order = get_object_or_404(Order, OrderId=order_id)
    order.confirmDelivery()
    StockLog.objects.create(
        itemId=order.itemId, userId=request.user,
        changeType='Restock', quantityChanged=order.quantity,
        reason=f'Delivery confirmed for Order #{order.OrderId}',
    )
    messages.success(request, 'Delivery confirmed and stock updated.')
    return redirect('order_list')


# ---------- R-13 / R-14: Reports ----------

@admin_required
def report_view(request):
    report_data = None
    if request.method == 'POST':
        form = ReportFilterForm(request.POST)
        report_type = request.POST.get('type')
        if form.is_valid():
            start = form.cleaned_data['start_date']
            end = form.cleaned_data['end_date']
            logs = StockLog.objects.filter(
                changeType=report_type, changedAt__date__gte=start, changedAt__date__lte=end,
            )
            report_data = logs.values('itemId__name').annotate(total=Sum('quantityChanged'))
            Report.objects.create(
                type=report_type, generatedBy=request.user,
                dateRangeStart=start, dateRangeEnd=end,
            )
    else:
        form = ReportFilterForm()
    return render(request, 'inventory/report.html', {'form': form, 'report_data': report_data})
