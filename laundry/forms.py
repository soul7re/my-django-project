from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import BusinessSettings, ClothingItem, Customer, Laundryman, Order, Payment


class DateInput(forms.DateInput):
    input_type = "date"


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone_number", "email", "address", "notes"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class LaundrymanForm(forms.ModelForm):
    class Meta:
        model = Laundryman
        fields = ["name", "phone_number", "address", "active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "customer",
            "laundryman",
            "pickup_date",
            "date_sent_to_laundry",
            "expected_completion_date",
            "delivery_date",
            "status",
            "notes",
        ]
        widgets = {
            "pickup_date": DateInput(),
            "date_sent_to_laundry": DateInput(),
            "expected_completion_date": DateInput(),
            "delivery_date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        laundrymen = Laundryman.objects.filter(active=True)
        if self.instance.pk and self.instance.laundryman_id:
            laundrymen = Laundryman.objects.filter(
                id__in=list(laundrymen.values_list("id", flat=True))
                + [self.instance.laundryman_id]
            )
        self.fields["laundryman"].queryset = laundrymen
        recommended = Order.recommend_laundryman()
        if not self.instance.pk and recommended:
            self.fields["laundryman"].initial = recommended
            self.fields[
                "laundryman"
            ].help_text = f"Recommended by workload balancing: {recommended.name}"

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        laundryman = cleaned_data.get("laundryman")
        pickup_date = cleaned_data.get("pickup_date")
        date_sent_to_laundry = cleaned_data.get("date_sent_to_laundry")
        expected_completion_date = cleaned_data.get("expected_completion_date")
        delivery_date = cleaned_data.get("delivery_date")

        if date_sent_to_laundry and pickup_date and date_sent_to_laundry < pickup_date:
            self.add_error(
                "date_sent_to_laundry",
                "Date sent to laundry cannot be earlier than pickup date.",
            )
        if expected_completion_date and pickup_date and expected_completion_date < pickup_date:
            self.add_error(
                "expected_completion_date",
                "Expected completion date cannot be earlier than pickup date.",
            )
        if delivery_date and pickup_date and delivery_date < pickup_date:
            self.add_error("delivery_date", "Delivery date cannot be earlier than pickup date.")
        if status == Order.STATUS_CANCELLED and delivery_date:
            self.add_error("delivery_date", "Cancelled orders should not be scheduled for delivery.")
        if laundryman and not laundryman.active and status in Order.active_statuses():
            self.add_error("laundryman", "Inactive laundrymen cannot receive active orders.")
        return cleaned_data


ClothingItemFormSet = inlineformset_factory(
    Order,
    ClothingItem,
    fields=["clothing_type", "quantity", "description"],
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True,
    widgets={"description": forms.TextInput()},
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "payment_date", "payment_method", "reference", "status"]
        widgets = {"payment_date": DateInput()}

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop("order", None)
        super().__init__(*args, **kwargs)
        if self.order:
            self.fields["amount"].help_text = f"Outstanding balance: NGN {self.order.balance:,.2f}"

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount < 0:
            raise forms.ValidationError("Payment amount cannot be negative.")
        if self.order and amount > self.order.balance:
            raise forms.ValidationError("Payment cannot exceed the outstanding balance.")
        return amount


class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = BusinessSettings
        fields = ["price_per_item", "commission_per_item", "default_processing_days"]


class ReportFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=DateInput())
    end_date = forms.DateField(required=False, widget=DateInput())

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be earlier than start date.")
        return cleaned_data


class DateFilterForm(forms.Form):
    date = forms.DateField(required=False, widget=DateInput())

    def clean_date(self):
        return self.cleaned_data.get("date") or timezone.localdate()
