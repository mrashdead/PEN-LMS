"""
URL configuration for pen project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/workflow/', include('apps.workflow.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/persons/', include('apps.persons.urls')),
    path('api/academics/', include('apps.academics.urls')),
    # Dashboard
    path('dashboard/login/', core_views.DashboardLoginView.as_view(), name='dashboard-login'),
    path('dashboard/logout/', core_views.DashboardLogoutView.as_view(), name='dashboard-logout'),
    path('dashboard/', core_views.DashboardHomeView.as_view(), name='dashboard-home'),
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
]
