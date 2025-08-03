from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Seller, TransactionLog, CreditRequest
from .serializers import (
    ChargeSerializer, CreateSellerSerializer, SellerSerializer,
    CreditRequestSerializer, TransactionLogSerializer
)
from .tasks import process_charge_task


class CreateSellerAPIView(APIView):

    @swagger_auto_schema(
        operation_description="Create a new seller account",
        request_body=CreateSellerSerializer,
        responses={
            201: SellerSerializer,
            400: "Bad Request - Invalid input",
            401: "Authentication credentials were not provided or are invalid",
            403: "Permission denied - Admin only"
        },
        operation_summary="Create Seller",
        tags=['sellers']
    )
    def post(self, request):
        serializer = CreateSellerSerializer(data=request.data)
        if serializer.is_valid():
            try:
                seller = serializer.save()
                return Response(SellerSerializer(seller).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class CreditRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    @swagger_auto_schema(
        operation_description="Create a new credit request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount'],
            properties={
                'amount': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format='decimal',
                    description='Amount of credit to request'
                )
            }
        ),
        responses={
            201: CreditRequestSerializer,
            400: "Bad Request - Invalid amount",
            401: "Authentication credentials were not provided"
        },
        operation_summary="Create Credit Request",
        tags=['credit']
    )
    def post(self, request):
        try:
            # Get the seller directly from the authenticated user's token
            seller = request.user.seller
            
            serializer = CreditRequestSerializer(
                data={
                    'amount': request.data.get('amount'),
                    'seller': seller.pk
                    }
                )
            if serializer.is_valid():
                try:
                    with transaction.atomic():
                        credit_request = serializer.save(seller=seller)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except IntegrityError as e:
                    return Response(
                        {"error": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Seller.DoesNotExist:
            return Response(
                {"error": "No seller account found for this user"},
                status=status.HTTP_400_BAD_REQUEST
            )

class TransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @swagger_auto_schema(
        operation_description="Get transaction history",
        responses={
            200: TransactionLogSerializer(many=True),
            401: "Authentication credentials were not provided or are invalid"
        },
        operation_summary="List Transactions",
        manual_parameters=[
            openapi.Parameter(
                'start_date',
                openapi.IN_QUERY,
                description="Start date for filtering (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'end_date',
                openapi.IN_QUERY,
                description="End date for filtering (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        tags=['transactions']
    )
    def get(self, request):
        seller = request.user.seller
        transactions = TransactionLog.objects.filter(seller=seller)

        # Optional date filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)

        serializer = TransactionLogSerializer(transactions, many=True)
        return Response(serializer.data)

class ChargeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    @swagger_auto_schema(
        operation_description="Create a new charge request for a seller",
        request_body=ChargeSerializer,
        responses={
            202: openapi.Response(
                description="Charge request accepted",
                examples={
                    "application/json": {
                        "status": "Charge request accepted and is being processed."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request - invalid input",
            ),
            401: openapi.Response(
                description="Authentication credentials were not provided or are invalid"
            )
        },
        operation_summary="Create Charge Request",
        tags=['charges']
    )
    def post(self, request, *args, **kwargs):
        serializer = ChargeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        seller_id = request.user.seller.id

        # Offload the database operation to Celery
        process_charge_task.delay(
            seller_id=seller_id,
            amount_str=str(validated_data['amount']),
            phone_number=str(validated_data['phone_number']),
        )
        
        # Return an immediate response to the client
        return Response({"status": "Charge request accepted and is being processed."}, status=status.HTTP_202_ACCEPTED)
