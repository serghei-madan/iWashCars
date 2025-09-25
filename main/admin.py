from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Service, Booking, ServiceImage, Payment
from .stripe_utils import StripePaymentService

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
    list_display = ['__str__', 'service', 'booking_date', 'booking_time', 'booking_end_time', 'is_confirmed', 'payment_status']
    list_filter = ['booking_date', 'service', 'is_confirmed']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'booking_date'
    readonly_fields = ['booking_end_time', 'total_price', 'created_at', 'updated_at']

    def payment_status(self, obj):
        try:
            payment = obj.payment
            status_colors = {
                'pending': 'orange',
                'deposit_captured': 'blue',
                'fully_captured': 'green',
                'deposit_refunded': 'red',
                'cancelled': 'gray',
                'failed': 'red',
            }
            color = status_colors.get(payment.status, 'black')
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                payment.get_status_display()
            )
        except Payment.DoesNotExist:
            return format_html('<span style="color: red;">No Payment</span>')

    payment_status.short_description = 'Payment Status'

@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ['service', 'alt_text', 'is_primary', 'display_order', 'created_at']
    list_filter = ['service', 'is_primary']
    list_editable = ['is_primary', 'display_order']
    ordering = ['service', 'display_order']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'booking_info', 'status', 'deposit_amount_display', 'total_amount_display',
        'remaining_amount_display', 'created_at', 'payment_actions'
    ]
    list_filter = ['status', 'created_at', 'deposit_captured_at', 'fully_captured_at']
    search_fields = ['booking__first_name', 'booking__last_name', 'booking__email', 'stripe_payment_intent_id']
    readonly_fields = [
        'stripe_payment_intent_id', 'stripe_customer_id', 'created_at', 'updated_at',
        'deposit_captured_at', 'fully_captured_at', 'refunded_at'
    ]

    fieldsets = (
        ('Booking Information', {
            'fields': ('booking',)
        }),
        ('Payment Details', {
            'fields': ('status', 'deposit_amount', 'total_amount', 'remaining_amount')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deposit_captured_at', 'fully_captured_at', 'refunded_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

    actions = ['capture_remaining_amount', 'refund_deposit', 'cancel_authorization']

    def booking_info(self, obj):
        return format_html(
            '<strong>{}</strong><br>{}',
            obj.booking,
            obj.booking.service.name
        )
    booking_info.short_description = 'Booking'

    def deposit_amount_display(self, obj):
        return f"${obj.get_deposit_amount_dollars():.2f}"
    deposit_amount_display.short_description = 'Deposit'

    def total_amount_display(self, obj):
        return f"${obj.get_total_amount_dollars():.2f}"
    total_amount_display.short_description = 'Total'

    def remaining_amount_display(self, obj):
        return f"${obj.get_remaining_amount_dollars():.2f}"
    remaining_amount_display.short_description = 'Remaining'

    def payment_actions(self, obj):
        actions = []

        if obj.can_capture_remaining():
            actions.append('✅ Can Finalize Payment')
        if obj.can_refund_deposit():
            actions.append('💸 Can Refund Deposit')
        if obj.can_cancel_authorization():
            actions.append('❌ Can Cancel Auth')

        return format_html('<br>'.join(actions)) if actions else 'No actions available'
    payment_actions.short_description = 'Available Actions'

    def capture_remaining_amount(self, request, queryset):
        """Admin action to capture remaining amount after service completion"""
        successful = 0
        failed = 0

        for payment in queryset:
            if payment.can_capture_remaining():
                result = StripePaymentService.capture_remaining_amount(payment)
                if result['success']:
                    successful += 1
                    self.message_user(request, f"✅ {payment.booking}: {result['message']}")
                else:
                    failed += 1
                    self.message_user(request, f"❌ {payment.booking}: {result['error']}", level='ERROR')
            else:
                failed += 1
                self.message_user(request, f"⚠️ {payment.booking}: Cannot capture remaining amount in current status", level='WARNING')

        if successful:
            self.message_user(request, f"Successfully captured remaining amount for {successful} payment(s)")
        if failed:
            self.message_user(request, f"Failed to process {failed} payment(s)", level='WARNING')

    capture_remaining_amount.short_description = "Finalize payment (capture remaining amount)"

    def refund_deposit(self, request, queryset):
        """Admin action to refund deposit in case of service issues"""
        successful = 0
        failed = 0

        for payment in queryset:
            if payment.can_refund_deposit():
                result = StripePaymentService.refund_deposit(payment, "Service issue - refunded by admin")
                if result['success']:
                    successful += 1
                    self.message_user(request, f"✅ {payment.booking}: {result['message']}")
                else:
                    failed += 1
                    self.message_user(request, f"❌ {payment.booking}: {result['error']}", level='ERROR')
            else:
                failed += 1
                self.message_user(request, f"⚠️ {payment.booking}: Cannot refund deposit in current status", level='WARNING')

        if successful:
            self.message_user(request, f"Successfully refunded deposit for {successful} payment(s)")
        if failed:
            self.message_user(request, f"Failed to process {failed} payment(s)", level='WARNING')

    refund_deposit.short_description = "Refund deposit to customer"

    def cancel_authorization(self, request, queryset):
        """Admin action to cancel authorization and release held funds"""
        successful = 0
        failed = 0

        for payment in queryset:
            if payment.can_cancel_authorization():
                result = StripePaymentService.cancel_authorization(payment)
                if result['success']:
                    successful += 1
                    self.message_user(request, f"✅ {payment.booking}: {result['message']}")
                else:
                    failed += 1
                    self.message_user(request, f"❌ {payment.booking}: {result['error']}", level='ERROR')
            else:
                failed += 1
                self.message_user(request, f"⚠️ {payment.booking}: Cannot cancel authorization in current status", level='WARNING')

        if successful:
            self.message_user(request, f"Successfully cancelled authorization for {successful} payment(s)")
        if failed:
            self.message_user(request, f"Failed to process {failed} payment(s)", level='WARNING')

    cancel_authorization.short_description = "Cancel authorization (release held funds)"
