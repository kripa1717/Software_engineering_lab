from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    InventoryItem,
    Vendor,
    Order,
    Alert,
    Forecast,
    Report,
    StockLog,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('itemID', 'name', 'unit', 'quantity', 'minThreshold', 'expirydate')
    search_fields = ('name',)
    list_filter = ('unit',)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendorID', 'name', 'ContactNumber', 'email', 'qualityRating')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('OrderId', 'itemId', 'vendorId', 'quantity', 'totalCost', 'status', 'orderDate')
    list_filter = ('status',)
    date_hierarchy = 'orderDate'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alertId', 'type', 'itemId', 'IsRead', 'createdAt')
    list_filter = ('type', 'IsRead')


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('forecastid', 'periodstart', 'periodend', 'generatedAt')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reportId', 'type', 'generatedBy', 'dateRangeStart', 'dateRangeEnd')
    list_filter = ('type',)


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ('logId', 'itemId', 'userId', 'changeType', 'quantityChanged', 'changedAt')
    list_filter = ('changeType',)
    date_hierarchy = 'changedAt'
