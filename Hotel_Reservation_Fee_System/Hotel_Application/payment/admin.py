from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'hotel', 'amount_paid', 'payment_date', 'payment_method')
    search_fields = ('booking__guest__name',)
    list_filter = ('hotel', 'payment_method', 'payment_date')
