from django.contrib import admin
from .models import Offer

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'company', 'role', 'package', 'offer_date')
    search_fields = ('student__name', 'company__name', 'role')
    list_filter = ('company', 'offer_date')
    list_per_page = 10
