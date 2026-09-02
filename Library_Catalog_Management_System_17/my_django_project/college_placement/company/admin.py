from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'industry', 'location', 'website')
    search_fields = ('name', 'industry', 'location')
    list_per_page = 10
