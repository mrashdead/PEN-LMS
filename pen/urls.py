"""
URL configuration for pen project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core import views as core_views

urlpatterns = [
    path('healthz/', core_views.healthz, name='healthz'),
    path('readyz/', core_views.readyz, name='readyz'),
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[]), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
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
    path('api/playhouse/', include('apps.playhouse.urls')),
    path('api/leads/', include('apps.leads.urls')),

    # Forms UI pages (session auth, dashboard-style)
    path('forms/', include('apps.forms.page_urls')),

    # Playhouse operator page (session auth, dashboard-style)
    path('playhouse/', include('apps.playhouse.page_urls')),
    path('leads/', include('apps.leads.page_urls')),

    # Dashboard workspace pages (persons / education / reports)
    path('workspace/', include('apps.core.page_urls')),

    # Password management
    path('api/auth/password/change/', core_views.DashboardPasswordChangeView.as_view(), name='password-change'),
    path('api/auth/password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html',
    ), name='password-change-done'),
    path('dashboard/password/reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url=reverse_lazy('password-reset-done'),
    ), name='password-reset'),
    path('dashboard/password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password-reset-done'),
    path('dashboard/password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('password-reset-complete'),
    ), name='password-reset-confirm'),
    path('dashboard/password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password-reset-complete'),

    # Dashboard
    path('dashboard/login/', core_views.DashboardLoginView.as_view(), name='dashboard-login'),
    path('dashboard/logout/', core_views.DashboardLogoutView.as_view(), name='dashboard-logout'),
    path('dashboard/', core_views.DashboardHomeView.as_view(), name='dashboard-home'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
]
