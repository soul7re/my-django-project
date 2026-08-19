from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-]{7,20}$",
    message="Enter a valid phone number.",
)


class Customer(models.Model):
    name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)
    address = models.TextField()
    date_registered = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(name=""),
                name="customer_name_not_blank",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("customer_detail", args=[self.pk])

    @property
    def total_spent(self):
        return self.orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    @property
    def outstanding_balance(self):
        return sum(order.balance for order in self.orders.all())


class Laundryman(models.Model):
    name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    address = models.TextField()
    active = models.BooleanField(default=True)
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(name=""),
                name="laundryman_name_not_blank",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("laundryman_detail", args=[self.pk])

    @property
    def active_orders_count(self):
        return self.orders.filter(status__in=Order.active_statuses()).count()

    @property
    def completed_orders_count(self):
        return self.orders.filter(status=Order.STATUS_DELIVERED).count()

    @property
    def total_items_processed(self):
        return (
            self.orders.filter(status=Order.STATUS_DELIVERED).aggregate(total=Sum("total_items"))[
                "total"
            ]
            or 0
        )


class BusinessSettings(models.Model):
    price_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("500.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    commission_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("100.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    default_processing_days = models.PositiveIntegerField(default=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Business settings"
        verbose_name_plural = "Business settings"
        constraints = [
            models.CheckConstraint(
                condition=Q(price_per_item__gte=0),
                name="settings_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(commission_per_item__gte=0),
                name="settings_commission_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(commission_per_item__lte=models.F("price_per_item")),
                name="settings_commission_not_above_price",
            ),
        ]

    def __str__(self):
        return "LaundryFlow business settings"

    def clean(self):
        if self.commission_per_item > self.price_per_item:
            raise ValidationError("Commission per item cannot exceed price per item.")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        settings, _created = cls.objects.get_or_create(pk=1)
        return settings


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PICKUP_SCHEDULED = "pickup_scheduled"
    STATUS_PICKED_UP = "picked_up"
    STATUS_SENT_TO_LAUNDRY = "sent_to_laundry"
    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready_for_pickup"
    STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PICKUP_SCHEDULED, "Pickup Scheduled"),
        (STATUS_PICKED_UP, "Picked Up"),
        (STATUS_SENT_TO_LAUNDRY, "Sent to Laundry"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_READY, "Ready for Pickup"),
        (STATUS_OUT_FOR_DELIVERY, "Out for Delivery"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PRIORITY_CRITICAL = "critical"
    PRIORITY_HIGH = "high"
    PRIORITY_NORMAL = "normal"
    PRIORITY_LOW = "low"

    PRIORITY_CHOICES = [
        (PRIORITY_CRITICAL, "Critical"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_LOW, "Low"),
    ]

    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PARTIAL = "partial"
    PAYMENT_PAID = "paid"

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PARTIAL, "Partially Paid"),
        (PAYMENT_PAID, "Paid"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    laundryman = models.ForeignKey(
        Laundryman,
        on_delete=models.PROTECT,
        related_name="orders",
        blank=True,
        null=True,
    )
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    order_date = models.DateField(default=timezone.localdate)
    pickup_date = models.DateField()
    date_sent_to_laundry = models.DateField(blank=True, null=True)
    expected_completion_date = models.DateField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_UNPAID,
    )
    total_items = models.PositiveIntegerField(default=0)
    price_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    commission_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    laundryman_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-order_date", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price_per_item__gte=0),
                name="order_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(commission_per_item__gte=0),
                name="order_commission_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="order_total_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(total_commission__gte=0),
                name="order_total_commission_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(laundryman_amount__gte=0),
                name="order_laundryman_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(commission_per_item__lte=models.F("price_per_item")),
                name="order_commission_not_above_price",
            ),
        ]

    def __str__(self):
        return self.order_number or "New order"

    def get_absolute_url(self):
        return reverse("order_detail", args=[self.pk])

    @classmethod
    def active_statuses(cls):
        return [
            cls.STATUS_PENDING,
            cls.STATUS_PICKUP_SCHEDULED,
            cls.STATUS_PICKED_UP,
            cls.STATUS_SENT_TO_LAUNDRY,
            cls.STATUS_PROCESSING,
            cls.STATUS_READY,
            cls.STATUS_OUT_FOR_DELIVERY,
        ]

    @classmethod
    def recommend_laundryman(cls):
        return (
            Laundryman.objects.filter(active=True)
            .annotate(
                active_workload=Count(
                    "orders",
                    filter=Q(orders__status__in=cls.active_statuses()),
                )
            )
            .order_by("active_workload", "date_registered", "name")
            .first()
        )

    @classmethod
    def priority_ordering(cls):
        return models.Case(
            models.When(priority=cls.PRIORITY_CRITICAL, then=0),
            models.When(priority=cls.PRIORITY_HIGH, then=1),
            models.When(priority=cls.PRIORITY_NORMAL, then=2),
            default=3,
            output_field=models.IntegerField(),
        )

    @classmethod
    def generate_order_number(cls):
        latest = cls.objects.order_by("-id").first()
        next_number = 1 if latest is None else latest.id + 1
        while True:
            order_number = f"LF{next_number:04d}"
            if not cls.objects.filter(order_number=order_number).exists():
                return order_number
            next_number += 1

    @property
    def amount_paid(self):
        if not self.pk:
            return Decimal("0.00")
        return (
            self.payments.filter(status=Payment.STATUS_COMPLETED).aggregate(total=Sum("amount"))[
                "total"
            ]
            or Decimal("0.00")
        )

    @property
    def balance(self):
        return max(self.total_amount - self.amount_paid, Decimal("0.00"))

    @property
    def is_overdue(self):
        return (
            self.delivery_date is not None
            and self.delivery_date < timezone.localdate()
            and self.status not in [self.STATUS_DELIVERED, self.STATUS_CANCELLED]
        )

    def calculate_priority(self):
        today = timezone.localdate()
        if self.is_overdue:
            return self.PRIORITY_CRITICAL
        if self.delivery_date and self.delivery_date <= today + timedelta(days=1):
            return self.PRIORITY_HIGH
        if self.delivery_date and self.delivery_date <= today + timedelta(days=7):
            return self.PRIORITY_NORMAL
        return self.PRIORITY_LOW if not self.delivery_date else self.PRIORITY_NORMAL

    def clean(self):
        errors = {}
        if self.pickup_date and self.expected_completion_date:
            if self.expected_completion_date < self.pickup_date:
                errors["expected_completion_date"] = (
                    "Expected completion date cannot be earlier than pickup date."
                )
        if self.pickup_date and self.date_sent_to_laundry:
            if self.date_sent_to_laundry < self.pickup_date:
                errors["date_sent_to_laundry"] = (
                    "Date sent to laundry cannot be earlier than pickup date."
                )
        if self.pickup_date and self.delivery_date:
            if self.delivery_date < self.pickup_date:
                errors["delivery_date"] = "Delivery date cannot be earlier than pickup date."
        if self.status == self.STATUS_CANCELLED and self.delivery_date:
            errors["delivery_date"] = "Cancelled orders should not be scheduled for delivery."
        if (
            self.laundryman
            and not self.laundryman.active
            and self.status in self.active_statuses()
        ):
            errors["laundryman"] = "Inactive laundrymen cannot receive active orders."
        if self.commission_per_item > self.price_per_item and self.price_per_item:
            errors["commission_per_item"] = "Commission cannot exceed price per item."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        settings = BusinessSettings.get_current()
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if not self.price_per_item:
            self.price_per_item = settings.price_per_item
        if not self.commission_per_item:
            self.commission_per_item = settings.commission_per_item
        if not self.expected_completion_date and self.pickup_date:
            self.expected_completion_date = self.pickup_date + timedelta(
                days=settings.default_processing_days
            )
        self.priority = self.calculate_priority()
        super().save(*args, **kwargs)

    def recalculate_totals(self):
        if not self.pk:
            return
        total_items = self.clothing_items.aggregate(total=Sum("quantity"))["total"] or 0
        total_amount = Decimal(total_items) * self.price_per_item
        total_commission = Decimal(total_items) * self.commission_per_item
        laundryman_amount = total_amount - total_commission
        paid = self.amount_paid
        if paid <= 0:
            payment_status = self.PAYMENT_UNPAID
        elif paid >= total_amount and total_amount > 0:
            payment_status = self.PAYMENT_PAID
        else:
            payment_status = self.PAYMENT_PARTIAL

        Order.objects.filter(pk=self.pk).update(
            total_items=total_items,
            total_amount=total_amount,
            total_commission=total_commission,
            laundryman_amount=laundryman_amount,
            payment_status=payment_status,
            priority=self.calculate_priority(),
        )
        self.total_items = total_items
        self.total_amount = total_amount
        self.total_commission = total_commission
        self.laundryman_amount = laundryman_amount
        self.payment_status = payment_status


class ClothingItem(models.Model):
    TYPE_SHIRT = "shirt"
    TYPE_TROUSERS = "trousers"
    TYPE_DRESS = "dress"
    TYPE_SKIRT = "skirt"
    TYPE_SUIT = "suit"
    TYPE_NATIVE = "native_wear"
    TYPE_BEDSHEET = "bedsheet"
    TYPE_OTHER = "other"

    CLOTHING_CHOICES = [
        (TYPE_SHIRT, "Shirt"),
        (TYPE_TROUSERS, "Trousers"),
        (TYPE_DRESS, "Dress"),
        (TYPE_SKIRT, "Skirt"),
        (TYPE_SUIT, "Suit"),
        (TYPE_NATIVE, "Native wear"),
        (TYPE_BEDSHEET, "Bedsheet"),
        (TYPE_OTHER, "Other"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="clothing_items")
    clothing_type = models.CharField(max_length=40, choices=CLOTHING_CHOICES)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["clothing_type"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="clothing_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="clothing_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.get_clothing_type_display()} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.price and self.order_id:
            self.price = self.order.price_per_item
        super().save(*args, **kwargs)
        self.order.recalculate_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        result = super().delete(*args, **kwargs)
        order.recalculate_totals()
        return result


class Payment(models.Model):
    METHOD_CASH = "cash"
    METHOD_TRANSFER = "transfer"
    METHOD_CARD = "card"
    METHOD_OTHER = "other"

    METHOD_CHOICES = [
        (METHOD_CASH, "Cash"),
        (METHOD_TRANSFER, "Bank Transfer"),
        (METHOD_CARD, "Card"),
        (METHOD_OTHER, "Other"),
    ]

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    payment_date = models.DateField(default=timezone.localdate)
    payment_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default=METHOD_CASH,
    )
    reference = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_COMPLETED)

    class Meta:
        ordering = ["-payment_date", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="payment_amount_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.recalculate_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        result = super().delete(*args, **kwargs)
        order.recalculate_totals()
        return result
