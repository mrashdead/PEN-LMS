"""
URL configuration for pen project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.authtoken.views import obtain_auth_token

from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # API Auth
    path('api/', include('rest_framework.urls')),
    path('api/auth/token/', obtain_auth_token, name='api-token-auth'),

    # Workflow / core API
    path('api/workflow/', include('apps.workflow.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/notifications/', include('apps.workflow.notification_urls')),
    path('api/persons/', include('apps.persons.urls')),
    path('api/academics/', include('apps.academics.urls')),
    path('api/education/', include('apps.education.urls')),
    path('api/forms/', include('apps.forms.urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/org/', include('apps.org.urls')),
    path('api/reports/', include('apps.reports.urls')),

    # Forms UI pages (session auth, dashboard-style)
    path('forms/', include('apps.forms.page_urls')),

    # Dashboard workspace pages (persons / education / reports)
    path('workspace/', include('apps.core.page_urls')),

    # Password management
    path('api/auth/password/change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url='/api/auth/password/done/',
    ), name='password-change'),
    path('api/auth/password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html',
    ), name='password-change-done'),

    # Dashboard
    path('dashboard/login/', core_views.DashboardLoginView.as_view(), name='dashboard-login'),
    path('dashboard/logout/', core_views.DashboardLogoutView.as_view(), name='dashboard-logout'),
    path('dashboard/', core_views.DashboardHomeView.as_view(), name='dashboard-home'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
]
