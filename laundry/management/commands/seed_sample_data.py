from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from laundry.models import BusinessSettings, ClothingItem, Customer, Laundryman, Order, Payment


class Command(BaseCommand):
    help = "Create realistic sample data for LaundryFlow."

    @transaction.atomic
    def handle(self, *args, **options):
        settings = BusinessSettings.get_current()
        settings.price_per_item = 500
        settings.commission_per_item = 100
        settings.default_processing_days = 2
        settings.save()

        customers = [
            Customer.objects.get_or_create(
                phone_number="+2348012345671",
                defaults={
                    "name": "Amina Yusuf",
                    "email": "amina@example.com",
                    "address": "Hall 2, University Road, Lagos",
                },
            )[0],
            Customer.objects.get_or_create(
                phone_number="+2348012345672",
                defaults={
                    "name": "Chinedu Okafor",
                    "email": "chinedu@example.com",
                    "address": "Block C, Students Lodge, Enugu",
                },
            )[0],
            Customer.objects.get_or_create(
                phone_number="+2348012345673",
                defaults={
                    "name": "Tolu Adeyemi",
                    "email": "tolu@example.com",
                    "address": "Room 14, Unity Hostel, Ibadan",
                },
            )[0],
        ]

        laundrymen = [
            Laundryman.objects.get_or_create(
                phone_number="+2348098765431",
                defaults={
                    "name": "Emeka Nwosu",
                    "address": "No. 8 Clean Street, Lagos",
                    "active": True,
                },
            )[0],
            Laundryman.objects.get_or_create(
                phone_number="+2348098765432",
                defaults={
                    "name": "Bala Mohammed",
                    "address": "Central Laundry Lane, Abuja",
                    "active": True,
                },
            )[0],
        ]

        today = timezone.localdate()
        samples = [
            {
                "order_number": "LF1001",
                "customer": customers[0],
                "laundryman": laundrymen[0],
                "pickup_date": today,
                "date_sent_to_laundry": today,
                "delivery_date": today + timedelta(days=1),
                "status": Order.STATUS_PICKUP_SCHEDULED,
                "items": [(ClothingItem.TYPE_SHIRT, 3), (ClothingItem.TYPE_TROUSERS, 2)],
                "payments": [1500],
            },
            {
                "order_number": "LF1002",
                "customer": customers[1],
                "laundryman": laundrymen[1],
                "pickup_date": today - timedelta(days=2),
                "date_sent_to_laundry": today - timedelta(days=1),
                "delivery_date": today,
                "status": Order.STATUS_PROCESSING,
                "items": [(ClothingItem.TYPE_DRESS, 1), (ClothingItem.TYPE_BEDSHEET, 2)],
                "payments": [],
            },
            {
                "order_number": "LF1003",
                "customer": customers[2],
                "laundryman": laundrymen[0],
                "pickup_date": today - timedelta(days=4),
                "date_sent_to_laundry": today - timedelta(days=3),
                "delivery_date": today - timedelta(days=1),
                "status": Order.STATUS_READY,
                "items": [(ClothingItem.TYPE_NATIVE, 2), (ClothingItem.TYPE_SKIRT, 1)],
                "payments": [1500],
            },
            {
                "order_number": "LF1004",
                "customer": customers[0],
                "laundryman": laundrymen[1],
                "pickup_date": today + timedelta(days=1),
                "date_sent_to_laundry": None,
                "delivery_date": today + timedelta(days=5),
                "status": Order.STATUS_PENDING,
                "items": [(ClothingItem.TYPE_SUIT, 1), (ClothingItem.TYPE_SHIRT, 2)],
                "payments": [],
            },
        ]

        for sample in samples:
            order, created = Order.objects.get_or_create(
                order_number=sample["order_number"],
                defaults={
                    "customer": sample["customer"],
                    "laundryman": sample["laundryman"],
                    "pickup_date": sample["pickup_date"],
                    "date_sent_to_laundry": sample["date_sent_to_laundry"],
                    "delivery_date": sample["delivery_date"],
                    "status": sample["status"],
                },
            )
            if not created:
                continue
            for clothing_type, quantity in sample["items"]:
                ClothingItem.objects.create(
                    order=order,
                    clothing_type=clothing_type,
                    quantity=quantity,
                )
            for amount in sample["payments"]:
                Payment.objects.create(order=order, amount=amount, payment_method=Payment.METHOD_TRANSFER)
            order.recalculate_totals()

        self.stdout.write(self.style.SUCCESS("Sample LaundryFlow data is ready."))
