from django.db import models

class Carrier(models.Model):
    """
    Model representing a motor carrier record retrieved from FMCSA QCMobile API.
    Designed to be compatible with MySQL and SQLite.
    """
    dot_number = models.BigIntegerField(unique=True, db_index=True)
    mc_number = models.BigIntegerField(null=True, blank=True, db_index=True)
    mc_prefix = models.CharField(max_length=10, null=True, blank=True)
    
    legal_name = models.CharField(max_length=255, null=True, blank=True)
    dba_name = models.CharField(max_length=255, null=True, blank=True)
    
    allowed_to_operate = models.BooleanField(null=True, blank=True)
    
    carrier_operation_code = models.CharField(max_length=50, null=True, blank=True)
    carrier_operation_description = models.CharField(max_length=255, null=True, blank=True)
    
    common_authority_status = models.CharField(max_length=50, null=True, blank=True)
    contract_authority_status = models.CharField(max_length=50, null=True, blank=True)
    broker_authority_status = models.CharField(max_length=50, null=True, blank=True)
    
    authorized_for_property = models.BooleanField(null=True, blank=True)
    authorized_for_broker = models.BooleanField(null=True, blank=True)
    authorized_for_household_goods = models.BooleanField(null=True, blank=True)
    authorized_for_passenger = models.BooleanField(null=True, blank=True)
    
    phy_street = models.CharField(max_length=255, null=True, blank=True)
    phy_city = models.CharField(max_length=100, null=True, blank=True)
    phy_state = models.CharField(max_length=50, null=True, blank=True)
    phy_zipcode = models.CharField(max_length=20, null=True, blank=True)
    phy_country = models.CharField(max_length=50, null=True, blank=True)
    
    total_drivers = models.IntegerField(null=True, blank=True)
    total_power_units = models.IntegerField(null=True, blank=True)
    
    bipd_insurance_on_file = models.CharField(max_length=50, null=True, blank=True)
    bipd_insurance_required = models.CharField(max_length=50, null=True, blank=True)
    bipd_required_amount = models.BigIntegerField(null=True, blank=True)
    
    cargo_insurance_on_file = models.CharField(max_length=50, null=True, blank=True)
    cargo_insurance_required = models.CharField(max_length=50, null=True, blank=True)
    
    bond_insurance_on_file = models.CharField(max_length=50, null=True, blank=True)
    bond_insurance_required = models.CharField(max_length=50, null=True, blank=True)
    
    crash_total = models.IntegerField(null=True, blank=True)
    fatal_crash = models.IntegerField(null=True, blank=True)
    inj_crash = models.IntegerField(null=True, blank=True)
    towaway_crash = models.IntegerField(null=True, blank=True)
    
    driver_insp = models.IntegerField(null=True, blank=True)
    driver_oos_insp = models.IntegerField(null=True, blank=True)
    driver_oos_rate = models.FloatField(null=True, blank=True)
    driver_oos_rate_national_average = models.FloatField(null=True, blank=True)
    
    vehicle_insp = models.IntegerField(null=True, blank=True)
    vehicle_oos_insp = models.IntegerField(null=True, blank=True)
    vehicle_oos_rate = models.FloatField(null=True, blank=True)
    vehicle_oos_rate_national_average = models.FloatField(null=True, blank=True)
    
    hazmat_insp = models.IntegerField(null=True, blank=True)
    hazmat_oos_insp = models.IntegerField(null=True, blank=True)
    hazmat_oos_rate = models.FloatField(null=True, blank=True)
    hazmat_oos_rate_national_average = models.FloatField(null=True, blank=True)
    
    safety_rating = models.CharField(max_length=100, null=True, blank=True)
    safety_rating_date = models.CharField(max_length=50, null=True, blank=True)
    
    oos_date = models.CharField(max_length=50, null=True, blank=True)
    status_code = models.CharField(max_length=50, null=True, blank=True)
    
    operation_classification = models.JSONField(default=list, blank=True)
    cargo_carried = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.legal_name or 'Carrier'} (DOT: {self.dot_number})"
