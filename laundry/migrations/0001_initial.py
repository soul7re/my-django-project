import decimal
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BusinessSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "price_per_item",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("500.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                (
                    "commission_per_item",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("100.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                ("default_processing_days", models.PositiveIntegerField(default=2)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Business settings",
                "verbose_name_plural": "Business settings",
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("price_per_item__gte", 0)), name="settings_price_non_negative"),
                    models.CheckConstraint(condition=models.Q(("commission_per_item__gte", 0)), name="settings_commission_non_negative"),
                    models.CheckConstraint(condition=models.Q(("commission_per_item__lte", models.F("price_per_item"))), name="settings_commission_not_above_price"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                (
                    "phone_number",
                    models.CharField(
                        max_length=20,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Enter a valid phone number.",
                                regex="^\\+?[0-9\\s\\-]{7,20}$",
                            )
                        ],
                    ),
                ),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.TextField()),
                ("date_registered", models.DateTimeField(auto_now_add=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("name", ""), _negated=True), name="customer_name_not_blank"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Laundryman",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                (
                    "phone_number",
                    models.CharField(
                        max_length=20,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Enter a valid phone number.",
                                regex="^\\+?[0-9\\s\\-]{7,20}$",
                            )
                        ],
                    ),
                ),
                ("address", models.TextField()),
                ("active", models.BooleanField(default=True)),
                ("date_registered", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["name"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("name", ""), _negated=True), name="laundryman_name_not_blank"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(blank=True, max_length=20, unique=True)),
                ("order_date", models.DateField(default=django.utils.timezone.localdate)),
                ("pickup_date", models.DateField()),
                ("date_sent_to_laundry", models.DateField(blank=True, null=True)),
                ("expected_completion_date", models.DateField(blank=True, null=True)),
                ("delivery_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("pickup_scheduled", "Pickup Scheduled"),
                            ("picked_up", "Picked Up"),
                            ("sent_to_laundry", "Sent to Laundry"),
                            ("processing", "Processing"),
                            ("ready_for_pickup", "Ready for Pickup"),
                            ("out_for_delivery", "Out for Delivery"),
                            ("delivered", "Delivered"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=30,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("critical", "Critical"),
                            ("high", "High"),
                            ("normal", "Normal"),
                            ("low", "Low"),
                        ],
                        default="normal",
                        max_length=20,
                    ),
                ),
                (
                    "payment_status",
                    models.CharField(
                        choices=[("unpaid", "Unpaid"), ("partial", "Partially Paid"), ("paid", "Paid")],
                        default="unpaid",
                        max_length=20,
                    ),
                ),
                ("total_items", models.PositiveIntegerField(default=0)),
                (
                    "price_per_item",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                (
                    "commission_per_item",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                (
                    "total_commission",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                (
                    "laundryman_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="laundry.customer",
                    ),
                ),
                (
                    "laundryman",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="laundry.laundryman",
                    ),
                ),
            ],
            options={
                "ordering": ["-order_date", "-created_at"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("price_per_item__gte", 0)), name="order_price_non_negative"),
                    models.CheckConstraint(condition=models.Q(("commission_per_item__gte", 0)), name="order_commission_non_negative"),
                    models.CheckConstraint(condition=models.Q(("total_amount__gte", 0)), name="order_total_amount_non_negative"),
                    models.CheckConstraint(condition=models.Q(("total_commission__gte", 0)), name="order_total_commission_non_negative"),
                    models.CheckConstraint(condition=models.Q(("laundryman_amount__gte", 0)), name="order_laundryman_amount_non_negative"),
                    models.CheckConstraint(condition=models.Q(("commission_per_item__lte", models.F("price_per_item"))), name="order_commission_not_above_price"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                ("payment_date", models.DateField(default=django.utils.timezone.localdate)),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("cash", "Cash"),
                            ("transfer", "Bank Transfer"),
                            ("card", "Card"),
                            ("other", "Other"),
                        ],
                        default="cash",
                        max_length=20,
                    ),
                ),
                ("reference", models.CharField(blank=True, max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")],
                        default="completed",
                        max_length=20,
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="laundry.order",
                    ),
                ),
            ],
            options={
                "ordering": ["-payment_date", "-id"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("amount__gte", 0)), name="payment_amount_non_negative"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ClothingItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "clothing_type",
                    models.CharField(
                        choices=[
                            ("shirt", "Shirt"),
                            ("trousers", "Trousers"),
                            ("dress", "Dress"),
                            ("skirt", "Skirt"),
                            ("suit", "Suit"),
                            ("native_wear", "Native wear"),
                            ("bedsheet", "Bedsheet"),
                            ("other", "Other"),
                        ],
                        max_length=40,
                    ),
                ),
                ("quantity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clothing_items",
                        to="laundry.order",
                    ),
                ),
            ],
            options={
                "ordering": ["clothing_type"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("quantity__gte", 1)), name="clothing_quantity_positive"),
                    models.CheckConstraint(condition=models.Q(("price__gte", 0)), name="clothing_price_non_negative"),
                ],
            },
        ),
    ]
