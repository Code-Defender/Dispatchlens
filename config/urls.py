from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('carriers.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('generator/', TemplateView.as_view(template_name='index.html'), name='generator'),
    path('refund-policy/', TemplateView.as_view(template_name='index.html'), name='refund-policy'),
    path('terms/', TemplateView.as_view(template_name='index.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='index.html'), name='privacy-policy'),
]
