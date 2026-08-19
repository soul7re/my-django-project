from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BusinessSettingsForm,
    ClothingItemFormSet,
    CustomerForm,
    DateFilterForm,
    LaundrymanForm,
    OrderForm,
    PaymentForm,
    ReportFilterForm,
)
from .models import BusinessSettings, Customer, Laundryman, Order, Payment


def paginate(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def parse_date(value):
    if not value:
        return None
    try:
        return timezone.datetime.fromisoformat(value).date()
    except ValueError:
        return None


def refresh_priorities():
    for order in Order.objects.filter(status__in=Order.active_statuses()):
        priority = order.calculate_priority()
        if priority != order.priority:
            Order.objects.filter(pk=order.pk).update(priority=priority)


@login_required
def dashboard(request):
    refresh_priorities()
    today = timezone.localdate()
    orders = Order.objects.select_related("customer", "laundryman")
    completed_payments = Payment.objects.filter(status=Payment.STATUS_COMPLETED)

    stats = {
        "today_pickups": orders.filter(pickup_date=today).count(),
        "today_deliveries": orders.filter(delivery_date=today).count(),
        "pending_orders": orders.filter(status=Order.STATUS_PENDING).count(),
        "processing_orders": orders.filter(status=Order.STATUS_PROCESSING).count(),
        "ready_orders": orders.filter(status=Order.STATUS_READY).count(),
        "total_orders": orders.count(),
        "delivered_orders": orders.filter(status=Order.STATUS_DELIVERED).count(),
        "cancelled_orders": orders.filter(status=Order.STATUS_CANCELLED).count(),
        "total_revenue": orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00"),
        "total_commission": orders.aggregate(total=Sum("total_commission"))["total"]
        or Decimal("0.00"),
        "laundrymen_earnings": orders.aggregate(total=Sum("laundryman_amount"))["total"]
        or Decimal("0.00"),
        "total_paid": completed_payments.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00"),
    }
    stats["outstanding_balances"] = stats["total_revenue"] - stats["total_paid"]

    priority_orders = (
        orders.exclude(status__in=[Order.STATUS_DELIVERED, Order.STATUS_CANCELLED])
        .annotate(priority_rank=Order.priority_ordering())
        .order_by("priority_rank", "delivery_date", "order_date")[:6]
    )

    context = {
        "stats": stats,
        "today_pickups": orders.filter(pickup_date=today).order_by("customer__name")[:5],
        "today_deliveries": orders.filter(delivery_date=today).order_by("customer__name")[:5],
        "priority_orders": priority_orders,
    }
    return render(request, "laundry/dashboard.html", context)


@login_required
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.annotate(order_count=Count("orders")).order_by("name")
    if query:
        customers = customers.filter(
            Q(name__icontains=query)
            | Q(phone_number__icontains=query)
            | Q(email__icontains=query)
            | Q(address__icontains=query)
        )
    return render(
        request,
        "laundry/customer_list.html",
        {"customers": paginate(request, customers), "query": query},
    )


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.orders.select_related("laundryman").order_by("-order_date")
    return render(request, "laundry/customer_detail.html", {"customer": customer, "orders": orders})


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        messages.success(request, "Customer created successfully.")
        return redirect(customer)
    return render(request, "laundry/form.html", {"form": form, "title": "Add Customer"})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        messages.success(request, "Customer updated successfully.")
        return redirect(customer)
    return render(request, "laundry/form.html", {"form": form, "title": "Edit Customer"})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        try:
            customer.delete()
            messages.success(request, "Customer deleted successfully.")
            return redirect("customer_list")
        except ProtectedError:
            messages.error(request, "Customers with orders cannot be deleted.")
    return render(request, "laundry/confirm_delete.html", {"object": customer, "title": "Delete Customer"})


@login_required
def laundryman_list(request):
    query = request.GET.get("q", "").strip()
    laundrymen = Laundryman.objects.annotate(
        active_workload=Count("orders", filter=Q(orders__status__in=Order.active_statuses())),
        completed_count=Count("orders", filter=Q(orders__status=Order.STATUS_DELIVERED)),
    ).order_by("name")
    if query:
        laundrymen = laundrymen.filter(
            Q(name__icontains=query) | Q(phone_number__icontains=query) | Q(address__icontains=query)
        )
    return render(
        request,
        "laundry/laundryman_list.html",
        {"laundrymen": paginate(request, laundrymen), "query": query},
    )


@login_required
def laundryman_detail(request, pk):
    laundryman = get_object_or_404(Laundryman, pk=pk)
    orders = laundryman.orders.select_related("customer").order_by("-order_date")
    return render(
        request,
        "laundry/laundryman_detail.html",
        {"laundryman": laundryman, "orders": orders},
    )


@login_required
def laundryman_create(request):
    form = LaundrymanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        laundryman = form.save()
        messages.success(request, "Laundryman created successfully.")
        return redirect(laundryman)
    return render(request, "laundry/form.html", {"form": form, "title": "Add Laundryman"})


@login_required
def laundryman_update(request, pk):
    laundryman = get_object_or_404(Laundryman, pk=pk)
    form = LaundrymanForm(request.POST or None, instance=laundryman)
    if request.method == "POST" and form.is_valid():
        laundryman = form.save()
        messages.success(request, "Laundryman updated successfully.")
        return redirect(laundryman)
    return render(request, "laundry/form.html", {"form": form, "title": "Edit Laundryman"})


@login_required
def laundryman_deactivate(request, pk):
    laundryman = get_object_or_404(Laundryman, pk=pk)
    if request.method == "POST":
        laundryman.active = False
        laundryman.save(update_fields=["active"])
        messages.success(request, "Laundryman deactivated.")
        return redirect("laundryman_detail", pk=laundryman.pk)
    return render(
        request,
        "laundry/confirm_delete.html",
        {"object": laundryman, "title": "Deactivate Laundryman", "action_label": "Deactivate"},
    )


@login_required
def order_list(request):
    refresh_priorities()
    orders = Order.objects.select_related("customer", "laundryman").annotate(
        priority_rank=Order.priority_ordering()
    )
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    payment_status = request.GET.get("payment_status", "").strip()
    priority = request.GET.get("priority", "").strip()
    pickup_date = parse_date(request.GET.get("pickup_date"))
    delivery_date = parse_date(request.GET.get("delivery_date"))

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(customer__name__icontains=query)
            | Q(laundryman__name__icontains=query)
        )
    if status:
        orders = orders.filter(status=status)
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    if priority:
        orders = orders.filter(priority=priority)
    if pickup_date:
        orders = orders.filter(pickup_date=pickup_date)
    if delivery_date:
        orders = orders.filter(delivery_date=delivery_date)

    orders = orders.order_by("priority_rank", "delivery_date", "-order_date")
    context = {
        "orders": paginate(request, orders),
        "query": query,
        "querystring": request.GET.copy(),
        "filters": {
            "status": status,
            "payment_status": payment_status,
            "priority": priority,
            "pickup_date": request.GET.get("pickup_date", ""),
            "delivery_date": request.GET.get("delivery_date", ""),
        },
        "status_choices": Order.STATUS_CHOICES,
        "payment_choices": Order.PAYMENT_STATUS_CHOICES,
        "priority_choices": Order.PRIORITY_CHOICES,
    }
    return render(request, "laundry/order_list.html", context)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("customer", "laundryman"), pk=pk)
    return render(
        request,
        "laundry/order_detail.html",
        {"order": order, "status_choices": Order.STATUS_CHOICES},
    )


@login_required
def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        formset = ClothingItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save()
                formset.instance = order
                formset.save()
                order.recalculate_totals()
            messages.success(request, f"Order {order.order_number} created successfully.")
            return redirect(order)
    else:
        form = OrderForm(initial={"pickup_date": timezone.localdate()})
        formset = ClothingItemFormSet()
    return render(
        request,
        "laundry/order_form.html",
        {"form": form, "formset": formset, "title": "Add Order"},
    )


@login_required
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        formset = ClothingItemFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save()
                formset.save()
                order.recalculate_totals()
            messages.success(request, f"Order {order.order_number} updated successfully.")
            return redirect(order)
    else:
        form = OrderForm(instance=order)
        formset = ClothingItemFormSet(instance=order)
    return render(
        request,
        "laundry/order_form.html",
        {"form": form, "formset": formset, "title": f"Edit {order.order_number}"},
    )


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect("order_list")
    return render(request, "laundry/confirm_delete.html", {"object": order, "title": "Delete Order"})


@login_required
def payment_create(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = PaymentForm(request.POST or None, order=order)
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.order = order
        payment.save()
        messages.success(request, "Payment recorded successfully.")
        return redirect(order)
    return render(
        request,
        "laundry/form.html",
        {"form": form, "title": f"Record Payment for {order.order_number}"},
    )


@login_required
def pickup_schedule(request):
    selected_date = timezone.localdate()
    form = DateFilterForm(request.GET or None, initial={"date": selected_date})
    if form.is_valid():
        selected_date = form.cleaned_data["date"]
    orders = (
        Order.objects.select_related("customer", "laundryman")
        .filter(pickup_date=selected_date)
        .annotate(priority_rank=Order.priority_ordering())
        .order_by("priority_rank", "customer__name")
    )
    return render(
        request,
        "laundry/pickup_schedule.html",
        {"form": form, "orders": orders, "selected_date": selected_date},
    )


@login_required
def processing_schedule(request):
    orders = (
        Order.objects.select_related("customer", "laundryman")
        .filter(
            status__in=[
                Order.STATUS_SENT_TO_LAUNDRY,
                Order.STATUS_PROCESSING,
                Order.STATUS_READY,
            ]
        )
        .annotate(priority_rank=Order.priority_ordering())
        .order_by("priority_rank", "expected_completion_date", "laundryman__name")
    )
    return render(request, "laundry/processing_schedule.html", {"orders": orders})


@login_required
def delivery_schedule(request):
    selected_date = timezone.localdate()
    form = DateFilterForm(request.GET or None, initial={"date": selected_date})
    if form.is_valid():
        selected_date = form.cleaned_data["date"]
    orders = (
        Order.objects.select_related("customer", "laundryman")
        .filter(delivery_date=selected_date)
        .annotate(priority_rank=Order.priority_ordering())
        .order_by("priority_rank", "customer__name")
    )
    return render(
        request,
        "laundry/delivery_schedule.html",
        {"form": form, "orders": orders, "selected_date": selected_date},
    )


@login_required
def reports(request):
    form = ReportFilterForm(request.GET or None)
    orders = Order.objects.all()
    payments = Payment.objects.filter(status=Payment.STATUS_COMPLETED)
    if form.is_valid():
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")
        if start_date:
            orders = orders.filter(order_date__gte=start_date)
            payments = payments.filter(payment_date__gte=start_date)
        if end_date:
            orders = orders.filter(order_date__lte=end_date)
            payments = payments.filter(payment_date__lte=end_date)

    total_revenue = orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_paid = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    report = {
        "total_orders": orders.count(),
        "total_clothes": orders.aggregate(total=Sum("total_items"))["total"] or 0,
        "total_revenue": total_revenue,
        "total_commission": orders.aggregate(total=Sum("total_commission"))["total"]
        or Decimal("0.00"),
        "laundrymen_earnings": orders.aggregate(total=Sum("laundryman_amount"))["total"]
        or Decimal("0.00"),
        "total_paid": total_paid,
        "outstanding_balances": total_revenue - total_paid,
    }
    return render(request, "laundry/reports.html", {"form": form, "report": report})


@login_required
def business_settings(request):
    settings = BusinessSettings.get_current()
    form = BusinessSettingsForm(request.POST or None, instance=settings)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Business settings updated successfully.")
        return redirect("business_settings")
    return render(request, "laundry/form.html", {"form": form, "title": "Business Settings"})
