from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def currency(value):
    try:
        amount = Decimal(value or 0)
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0.00")
    return f"NGN {amount:,.2f}"


@register.filter
def badge_class(value):
    mapping = {
        "critical": "badge-danger",
        "high": "badge-warning",
        "normal": "badge-info",
        "low": "badge-muted",
        "paid": "badge-success",
        "partial": "badge-warning",
        "unpaid": "badge-danger",
        "delivered": "badge-success",
        "cancelled": "badge-muted",
        "processing": "badge-info",
        "ready_for_pickup": "badge-success",
        "out_for_delivery": "badge-warning",
    }
    return mapping.get(value, "badge-muted")
