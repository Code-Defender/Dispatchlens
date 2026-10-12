from django.contrib import admin
from .models import Carrier

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ('dot_number', 'mc_number', 'legal_name', 'allowed_to_operate', 'phy_state', 'updated_at')
    search_fields = ('dot_number', 'mc_number', 'legal_name', 'dba_name')
    list_filter = ('allowed_to_operate', 'phy_state', 'common_authority_status')
