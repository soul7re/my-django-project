from django.urls import path

from . import views


urlpatterns = [
    path("accounts/signup/", views.signup, name="signup"),
    path("", views.dashboard, name="dashboard"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/add/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_update, name="customer_update"),
    path("customers/<int:pk>/delete/", views.customer_delete, name="customer_delete"),
    path("laundrymen/", views.laundryman_list, name="laundryman_list"),
    path("laundrymen/add/", views.laundryman_create, name="laundryman_create"),
    path("laundrymen/<int:pk>/", views.laundryman_detail, name="laundryman_detail"),
    path("laundrymen/<int:pk>/edit/", views.laundryman_update, name="laundryman_update"),
    path("laundrymen/<int:pk>/deactivate/", views.laundryman_deactivate, name="laundryman_deactivate"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/add/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/edit/", views.order_update, name="order_update"),
    path("orders/<int:pk>/delete/", views.order_delete, name="order_delete"),
    path("orders/<int:pk>/payments/add/", views.payment_create, name="payment_create"),
    path("schedule/pickups/", views.pickup_schedule, name="pickup_schedule"),
    path("schedule/processing/", views.processing_schedule, name="processing_schedule"),
    path("schedule/deliveries/", views.delivery_schedule, name="delivery_schedule"),
    path("reports/", views.reports, name="reports"),
    path("settings/", views.business_settings, name="business_settings"),
]
