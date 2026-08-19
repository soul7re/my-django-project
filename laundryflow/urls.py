"""Project URL configuration."""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("", include("laundry.urls")),
]


if settings.DEBUG or settings.STATICFILES_DIRS:
    # Serve local project assets during development and project demos.
    urlpatterns += [
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATICFILES_DIRS[0]},
        )
    ]
