from django.contrib import admin, messages
from django.db import transaction
from .models import Seller, CreditRequest, TransactionLog

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('name', 'credit')
    readonly_fields = ('credit',)

@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ('seller', 'transaction_type', 'amount', 'balance_after', 'created_at')
    list_filter = ('seller', 'transaction_type')
    readonly_fields = [f.name for f in TransactionLog._meta.fields] # All fields read-only

@admin.register(CreditRequest)
class CreditRequestAdmin(admin.ModelAdmin):
    list_display = ('seller', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['approve_requests']

    @admin.action(description='Approve selected credit requests')
    def approve_requests(self, request, queryset):
        """
        Admin action to approve credit requests.
        This operation is atomic to ensure data integrity[cite: 18].
        It prevents a request from being processed more than once[cite: 14].
        """
        # Filter for only pending requests to avoid re-approving
        pending_requests = queryset.filter(status='pending')
        
        for credit_request in pending_requests:
            try:
                with transaction.atomic():
                    # Lock the seller row to prevent race conditions during update
                    seller = Seller.objects.select_for_update().get(pk=credit_request.seller.id)
                    
                    # Increase seller's credit
                    seller.credit += credit_request.amount
                    seller.save()
                    
                    # Update request status
                    credit_request.status = 'approved'
                    credit_request.save()
                    
                    # Create a log for the transaction
                    TransactionLog.objects.create(
                        seller=seller,
                        transaction_type='add_credit',
                        amount=credit_request.amount,
                        balance_after=seller.credit
                    )
            except Exception as e:
                self.message_user(request, f"Error approving request for {credit_request.seller.name}: {e}", messages.ERROR)
        
        self.message_user(request, f"Successfully approved {pending_requests.count()} requests.", messages.SUCCESS)