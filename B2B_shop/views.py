from django.db import transaction, IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated 
from rest_framework.authentication import TokenAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Seller, TransactionLog
from .serializers import ChargeSerializer
from .tasks import process_charge_task


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
        
        # In a real app, use `request.user.id`
        seller_id = 1 

        # Offload the database operation to Celery
        process_charge_task.delay(
            seller_id=seller_id,
            amount_str=str(validated_data['amount']), # Pass Decimal as string
            unique_id=validated_data['unique_id']
        )
        
        # Return an immediate response to the client
        return Response({"status": "Charge request accepted and is being processed."}, status=status.HTTP_202_ACCEPTED)
