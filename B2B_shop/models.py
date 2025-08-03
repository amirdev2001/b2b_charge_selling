import uuid
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.contrib.auth.models import User

class Seller(models.Model):
    """
    Represents a seller with a credit balance[cite: 3].
    The credit can never be negative, enforced by a database constraint[cite: 6, 16].
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    # Using DecimalField for financial accuracy
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        constraints = [
            CheckConstraint(check=Q(credit__gte=0), name='credit_not_negative')
        ]

    def __str__(self):
        return f"{self.name} - Credit: {self.credit}"

class CreditRequest(models.Model):
    """
    A request from a seller to increase their credit, which requires admin approval[cite: 4].
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='credit_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request of {self.amount} for {self.seller.name} ({self.status})"


class Charge(models.Model):
    """
    Represents a charge initiated by a seller, e.g., for a product or service.
    Each charge has a unique UUID, seller, amount, phone number, status, and timestamp.
    The amount must always be positive.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='charges')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            CheckConstraint(check=Q(amount__gt=0), name='charge_amount_positive')
        ]

    def __str__(self):
        return f"Charge {self.amount} to {self.phone_number} by {self.seller.name} ({self.status})"


class TransactionLog(models.Model):
    """
    Logs every operation that changes a seller's credit to ensure accounting is verifiable[cite: 6, 7, 15].
    Includes a unique_id to prevent duplicate transactions (idempotency)[cite: 17].
    """
    TRANSACTION_TYPES = [
        ('add_credit', 'Add Credit'),
        ('charge_sale', 'Charge Sale'),
    ]
    # Using a UUID for the unique transaction identifier
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2) # Seller's balance after this tx
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.transaction_type}] {self.amount} for {self.seller.name}"
    