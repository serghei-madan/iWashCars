from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import VehicleType, Service, Booking, ServiceImage, Payment
from .stripe_utils import StripePaymentService

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_multiplier', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active']
    list_editable = ['price_multiplier', 'display_order', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price_multiplier')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'display_order']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'vehicle_type', 'tier', 'price', 'deposit_display', 'duration_minutes', 'display_order', 'is_active']
    list_filter = ['vehicle_type', 'tier', 'is_active']
    list_editable = ['vehicle_type', 'price', 'duration_minutes', 'display_order', 'is_active']
    ordering = ['vehicle_type', 'display_order', 'price']
    search_fields = ['name', 'description']
    inlines = [ServiceImageInline]

    def deposit_display(self, obj):
        """Display deposit amount in dollars"""
        return f"${obj.get_deposit_amount_dollars():.2f}"
    deposit_display.short_description = 'Deposit'

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'vehicle_type', 'tier', 'description', 'price', 'deposit_amount', 'duration_minutes'),
            'description': 'Select the vehicle type this service is available for. You can manage vehicle types in the Vehicle Types section.'
        }),
        ('Details', {
            'fields': ('features', 'details'),
            'description': 'Detailed service information and features'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the vehicle_type dropdown to show only active types"""
        if db_field.name == "vehicle_type":
            kwargs["queryset"] = VehicleType.objects.filter(is_active=True).order_by('display_order', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            'all': ('admin/css/hide-related-links.css',)
        }
        js = ('admin/js/hide-related-links.js',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'vehicle_type', 'service', 'booking_date', 'booking_time', 'booking_end_time', 'status_badge', 'is_confirmed', 'payment_status']
    list_filter = ['booking_date', 'vehicle_type', 'service', 'status', 'is_confirmed']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'booking_date'
    readonly_fields = ['booking_end_time', 'total_price', 'created_at', 'updated_at', 'cancelled_at']
    actions = ['complete_service_and_finalize_payment', 'cancel_booking', 'mark_completed', 'mark_no_show']

    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Service Details', {
            'fields': ('vehicle_type', 'service', 'booking_date', 'booking_time', 'booking_end_time', 'total_price')
        }),
        ('Location', {
            'fields': ('address', 'city', 'zip_code')
        }),
        ('Status', {
            'fields': ('status', 'is_confirmed', 'cancellation_reason', 'cancelled_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'reminder_sent', 'reminder_sent_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        status_colors = {
            'pending': '#FFA500',  # orange
            'confirmed': '#007BFF', # blue
            'completed': '#28A745', # green
            'cancelled': '#DC3545', # red
            'no_show': '#6C757D',   # gray
        }
        color = status_colors.get(obj.status, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

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

    def complete_service_and_finalize_payment(self, request, queryset):
        """Complete service and automatically finalize payment in one action"""
        successful = 0
        failed = 0
        already_completed = 0

        for booking in queryset:
            # Check if already completed
            if booking.status == 'completed':
                already_completed += 1
                self.message_user(request, f"⚠️  {booking}: Already completed", level='WARNING')
                continue

            # Check if booking can be completed (must be pending or confirmed)
            if booking.status not in ['pending', 'confirmed']:
                failed += 1
                self.message_user(
                    request,
                    f"⚠️  {booking}: Cannot complete - status is '{booking.get_status_display()}'",
                    level='WARNING'
                )
                continue

            try:
                # Try to capture payment first
                payment_result = None
                try:
                    payment = booking.payment

                    # Check if payment can be captured
                    if payment.can_capture_remaining():
                        payment_result = StripePaymentService.capture_remaining_amount(payment)

                        if not payment_result['success']:
                            # Payment failed - don't mark as completed
                            failed += 1
                            error_msg = payment_result.get('error', 'Unknown error')
                            self.message_user(
                                request,
                                f"❌ {booking}: Payment capture failed - {error_msg}. Booking NOT marked as completed.",
                                level='ERROR'
                            )
                            continue
                    elif payment.status == 'fully_captured':
                        # Already fully paid
                        payment_result = {'success': True, 'message': 'Payment already fully captured'}
                    else:
                        # Payment status doesn't allow capture
                        failed += 1
                        self.message_user(
                            request,
                            f"⚠️  {booking}: Cannot capture payment - status is '{payment.get_status_display()}'",
                            level='WARNING'
                        )
                        continue

                except Payment.DoesNotExist:
                    # No payment record - this shouldn't happen, but handle it
                    failed += 1
                    self.message_user(
                        request,
                        f"❌ {booking}: No payment record found. Cannot complete.",
                        level='ERROR'
                    )
                    continue

                # Payment successful or already captured - mark booking as completed
                booking.status = 'completed'
                booking.save()

                successful += 1
                payment_msg = f" | Payment: {payment_result.get('message', 'Completed')}" if payment_result else ""
                self.message_user(
                    request,
                    f"✅ {booking}: Service completed & payment finalized{payment_msg}",
                )

            except Exception as e:
                failed += 1
                self.message_user(
                    request,
                    f"❌ {booking}: Failed to complete - {str(e)}",
                    level='ERROR'
                )

        # Summary messages
        if successful:
            self.message_user(
                request,
                f"🎉 Successfully completed {successful} booking(s) and finalized payment(s)"
            )
        if already_completed:
            self.message_user(
                request,
                f"{already_completed} booking(s) were already completed",
                level='INFO'
            )
        if failed:
            self.message_user(
                request,
                f"⚠️  Failed to complete {failed} booking(s)",
                level='WARNING'
            )

    complete_service_and_finalize_payment.short_description = "✅ Complete service & finalize payment"

    def cancel_booking(self, request, queryset):
        """Cancel selected bookings and handle payments"""
        from .notification_utils import NotificationService

        successful = 0
        failed = 0

        for booking in queryset:
            if booking.status == 'cancelled':
                self.message_user(request, f"⚠️  {booking}: Already cancelled", level='WARNING')
                continue

            try:
                # Cancel/refund payment if exists
                payment_result = None
                try:
                    payment = booking.payment
                    if payment.status == 'deposit_captured':
                        # Cancel authorization and release held funds
                        payment_result = StripePaymentService.cancel_authorization(payment)
                        if not payment_result['success']:
                            # If can't cancel auth, try refund
                            if payment.can_refund_deposit():
                                payment_result = StripePaymentService.refund_deposit(
                                    payment,
                                    reason="Booking cancelled by admin"
                                )
                    elif payment.can_refund_deposit():
                        # Refund deposit if possible
                        payment_result = StripePaymentService.refund_deposit(
                            payment,
                            reason="Booking cancelled by admin"
                        )
                except Payment.DoesNotExist:
                    pass  # No payment to handle

                # Update booking status
                booking.status = 'cancelled'
                booking.cancelled_at = timezone.now()
                booking.cancellation_reason = 'Cancelled by admin'
                booking.save()

                # Send cancellation email
                try:
                    email_result = NotificationService.send_cancellation_notification(booking)
                    if not email_result['success']:
                        self.message_user(
                            request,
                            f"⚠️  {booking}: Cancelled but email failed: {email_result.get('error')}",
                            level='WARNING'
                        )
                except Exception as e:
                    self.message_user(
                        request,
                        f"⚠️  {booking}: Cancelled but email failed: {str(e)}",
                        level='WARNING'
                    )

                successful += 1
                payment_msg = ""
                if payment_result:
                    payment_msg = f" (Payment: {payment_result.get('message', 'handled')})"
                self.message_user(request, f"✅ {booking}: Cancelled successfully{payment_msg}")

            except Exception as e:
                failed += 1
                self.message_user(request, f"❌ {booking}: Failed to cancel - {str(e)}", level='ERROR')

        if successful:
            self.message_user(request, f"Successfully cancelled {successful} booking(s)")
        if failed:
            self.message_user(request, f"Failed to cancel {failed} booking(s)", level='WARNING')

    cancel_booking.short_description = "Cancel selected bookings (refund/release payment)"

    def mark_completed(self, request, queryset):
        """Mark bookings as completed"""
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(
            status='completed'
        )
        self.message_user(request, f"Marked {updated} booking(s) as completed")

    mark_completed.short_description = "Mark as completed"

    def mark_no_show(self, request, queryset):
        """Mark bookings as no-show (keep deposit)"""
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(
            status='no_show'
        )
        self.message_user(request, f"Marked {updated} booking(s) as no-show")

    mark_no_show.short_description = "Mark as no-show (keep deposit)"

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
        from .notification_utils import NotificationService

        successful = 0
        failed = 0

        for payment in queryset:
            if payment.can_cancel_authorization():
                result = StripePaymentService.cancel_authorization(payment)
                if result['success']:
                    # Also mark booking as cancelled
                    booking = payment.booking
                    if booking.status not in ['cancelled', 'completed']:
                        booking.status = 'cancelled'
                        booking.cancelled_at = timezone.now()
                        booking.cancellation_reason = 'Payment authorization cancelled by admin'
                        booking.save()

                        # Send cancellation notification
                        try:
                            NotificationService.send_cancellation_notification(booking)
                        except Exception as e:
                            self.message_user(
                                request,
                                f"⚠️ {payment.booking}: Payment cancelled but email failed: {str(e)}",
                                level='WARNING'
                            )

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

    cancel_authorization.short_description = "Cancel authorization (release held funds & cancel booking)"
