from django.urls import path
from .views import CarrierDetailView, CarrierSearchRangeView, CarrierSearchDateView

urlpatterns = [
    path('carriers/search/', CarrierSearchRangeView.as_view(), name='carrier-search'),
    path('carriers/search-by-date/', CarrierSearchDateView.as_view(), name='carrier-search-date'),
    path('carriers/<str:dot_number>/', CarrierDetailView.as_view(), name='carrier-detail'),
]
