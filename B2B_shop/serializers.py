from rest_framework import serializers
import uuid

class ChargeSerializer(serializers.Serializer):
    """
    Serializer for the phone charging endpoint[cite: 5].
    Validates amount, phone number, and the unique ID for idempotency[cite: 17].
    """
    phone_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    unique_id = serializers.UUIDField()