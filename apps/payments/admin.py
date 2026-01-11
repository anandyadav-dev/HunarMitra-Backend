from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Transaction, Payment, Payout

@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__phone', 'transaction_id')


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'gateway', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    search_fields = ('id', 'booking__id', 'gateway_reference')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Payout)
class PayoutAdmin(ModelAdmin):
    list_display = ('id', 'worker', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'worker__user__phone', 'worker__user__first_name')
    readonly_fields = ('created_at', 'updated_at')
