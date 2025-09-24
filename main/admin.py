from django.contrib import admin
from .models import Service, Booking, ServiceImage

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'display_order']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'price', 'duration_minutes', 'display_order', 'is_active']
    list_filter = ['tier', 'is_active']
    list_editable = ['price', 'duration_minutes', 'display_order', 'is_active']
    ordering = ['display_order', 'price']
    inlines = [ServiceImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'tier', 'description', 'price', 'duration_minutes')
        }),
        ('Details', {
            'fields': ('features', 'details'),
            'description': 'Detailed service information and features'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'service', 'booking_date', 'booking_time', 'booking_end_time', 'is_confirmed']
    list_filter = ['booking_date', 'service', 'is_confirmed']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'booking_date'
    readonly_fields = ['booking_end_time', 'total_price', 'created_at', 'updated_at']

@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ['service', 'alt_text', 'is_primary', 'display_order', 'created_at']
    list_filter = ['service', 'is_primary']
    list_editable = ['is_primary', 'display_order']
    ordering = ['service', 'display_order']
