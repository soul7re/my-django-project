from django.contrib import admin

from .models import BusinessSettings, ClothingItem, Customer, Laundryman, Order, Payment


class ClothingItemInline(admin.TabularInline):
    model = ClothingItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "email", "date_registered")
    search_fields = ("name", "phone_number", "email", "address")
    ordering = ("name",)


@admin.register(Laundryman)
class LaundrymanAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "active", "date_registered")
    list_filter = ("active",)
    search_fields = ("name", "phone_number", "address")
    ordering = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "laundryman",
        "status",
        "priority",
        "payment_status",
        "total_items",
        "total_amount",
        "date_sent_to_laundry",
        "delivery_date",
    )
    list_filter = (
        "status",
        "priority",
        "payment_status",
        "pickup_date",
        "date_sent_to_laundry",
        "delivery_date",
    )
    search_fields = ("order_number", "customer__name", "laundryman__name")
    readonly_fields = (
        "total_items",
        "total_amount",
        "total_commission",
        "laundryman_amount",
        "created_at",
        "updated_at",
    )
    inlines = [ClothingItemInline, PaymentInline]
    ordering = ("-order_date", "-created_at")


@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display = ("order", "clothing_type", "quantity", "price")
    list_filter = ("clothing_type",)
    search_fields = ("order__order_number", "description")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "payment_method", "payment_date", "status")
    list_filter = ("payment_method", "status", "payment_date")
    search_fields = ("order__order_number", "reference")


@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    list_display = ("price_per_item", "commission_per_item", "default_processing_days", "updated_at")

    def has_add_permission(self, request):
        return not BusinessSettings.objects.exists()
