from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import BusinessSettings, ClothingItem, Customer, Laundryman, Order, Payment


class LaundryFlowModelTests(TestCase):
    def setUp(self):
        self.settings = BusinessSettings.get_current()
        self.customer = Customer.objects.create(
            name="Amina Yusuf",
            phone_number="+2348012345671",
            email="amina@example.com",
            address="Hall 2, University Road",
        )
        self.laundryman = Laundryman.objects.create(
            name="Emeka Nwosu",
            phone_number="+2348098765431",
            address="No. 8 Clean Street",
        )

    def create_order(self, **kwargs):
        defaults = {
            "customer": self.customer,
            "laundryman": self.laundryman,
            "pickup_date": timezone.localdate(),
            "delivery_date": timezone.localdate() + timedelta(days=3),
            "status": Order.STATUS_PENDING,
        }
        defaults.update(kwargs)
        return Order.objects.create(**defaults)

    def test_customer_creation(self):
        self.assertEqual(str(self.customer), "Amina Yusuf")

    def test_laundryman_creation(self):
        self.assertTrue(self.laundryman.active)
        self.assertEqual(str(self.laundryman), "Emeka Nwosu")

    def test_order_creation_generates_number_and_completion_date(self):
        order = self.create_order()
        self.assertTrue(order.order_number.startswith("LF"))
        self.assertEqual(
            order.expected_completion_date,
            order.pickup_date + timedelta(days=self.settings.default_processing_days),
        )

    def test_clothing_item_creation(self):
        order = self.create_order()
        item = ClothingItem.objects.create(
            order=order,
            clothing_type=ClothingItem.TYPE_SHIRT,
            quantity=2,
        )
        self.assertEqual(item.quantity, 2)

    def test_total_item_calculation(self):
        order = self.create_order()
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_SHIRT, quantity=3)
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_TROUSERS, quantity=2)
        order.refresh_from_db()
        self.assertEqual(order.total_items, 5)

    def test_total_amount_calculation(self):
        order = self.create_order()
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_SHIRT, quantity=5)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal("2500.00"))

    def test_commission_calculation(self):
        order = self.create_order()
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_SHIRT, quantity=5)
        order.refresh_from_db()
        self.assertEqual(order.total_commission, Decimal("500.00"))

    def test_laundryman_earnings_calculation(self):
        order = self.create_order()
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_SHIRT, quantity=5)
        order.refresh_from_db()
        self.assertEqual(order.laundryman_amount, Decimal("2000.00"))

    def test_payment_balance_calculation(self):
        order = self.create_order()
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_SHIRT, quantity=5)
        Payment.objects.create(order=order, amount=Decimal("1500.00"))
        order.refresh_from_db()
        self.assertEqual(order.balance, Decimal("1000.00"))
        self.assertEqual(order.payment_status, Order.PAYMENT_PARTIAL)

    def test_paid_payment_status(self):
        order = self.create_order()
        ClothingItem.objects.create(order=order, clothing_type=ClothingItem.TYPE_SHIRT, quantity=2)
        Payment.objects.create(order=order, amount=Decimal("1000.00"))
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)

    def test_order_status(self):
        order = self.create_order(status=Order.STATUS_PROCESSING)
        self.assertEqual(order.status, Order.STATUS_PROCESSING)

    def test_priority_scheduling(self):
        order = self.create_order(delivery_date=timezone.localdate() - timedelta(days=1))
        self.assertEqual(order.priority, Order.PRIORITY_CRITICAL)

    def test_laundryman_workload_calculation(self):
        busy = self.laundryman
        available = Laundryman.objects.create(
            name="Bala Mohammed",
            phone_number="+2348098765432",
            address="Central Laundry Lane",
        )
        self.create_order(laundryman=busy, status=Order.STATUS_PROCESSING)
        self.assertEqual(Order.recommend_laundryman(), available)

    def test_inactive_laundryman_restriction(self):
        inactive = Laundryman.objects.create(
            name="Inactive Worker",
            phone_number="+2348098765433",
            address="Closed Shop",
            active=False,
        )
        order = Order(
            customer=self.customer,
            laundryman=inactive,
            pickup_date=timezone.localdate(),
            status=Order.STATUS_PENDING,
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_date_validation(self):
        order = Order(
            customer=self.customer,
            laundryman=self.laundryman,
            pickup_date=timezone.localdate(),
            delivery_date=timezone.localdate() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            order.full_clean()

    def test_date_sent_to_laundry_validation(self):
        order = Order(
            customer=self.customer,
            laundryman=self.laundryman,
            pickup_date=timezone.localdate(),
            date_sent_to_laundry=timezone.localdate() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            order.full_clean()


class LaundryFlowViewTests(TestCase):
    def test_authentication_protection(self):
        response = Client().get(reverse("customer_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_dashboard_access(self):
        user = User.objects.create_user(username="owner", password="pass12345")
        client = Client()
        self.assertTrue(client.login(username="owner", password="pass12345"))
        response = client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
