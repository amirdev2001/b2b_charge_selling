from rest_framework import serializers
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Seller, CreditRequest, TransactionLog
from decimal import Decimal
from .models import Seller, CreditRequest, TransactionLog

class ChargeSerializer(serializers.Serializer):
    """
    Serializer for the phone charging endpoint.
    Validates amount, phone number for idempotency.
    """
    phone_number = serializers.CharField(max_length=11)
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal("0.01")
    )

class CreateSellerSerializer(serializers.Serializer):
    """
    Serializer for creating new sellers with their user accounts.
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    name = serializers.CharField(max_length=100)

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        name = validated_data.pop('name')
        
        user = User.objects.create_user(username=username, password=password)
        seller = Seller.objects.create(user=user, name=name)
        return seller

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model, used within SellerSerializer.
    """
    class Meta:
        model = User
        fields = ('id', 'username')
        read_only_fields = ('id',)

class SellerSerializer(serializers.ModelSerializer):
    """
    Serializer for general seller operations.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Seller
        fields = ('id', 'user', 'name', 'credit')
        read_only_fields = ('id', 'credit')

class CreditRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for credit requests.
    """

    class Meta:
        model = CreditRequest
        fields = ('id', 'seller', 'amount', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'created_at', 'updated_at')

class TransactionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for transaction logs.
    """
    seller_name = serializers.CharField(source='seller.name', read_only=True)

    class Meta:
        model = TransactionLog
        fields = ('unique_id', 'seller', 'seller_name', 'transaction_type', 
                 'amount', 'balance_after', 'created_at')
        read_only_fields = ('unique_id', 'balance_after', 'created_at')