from django.urls import path
from .views import ChargeAPIView

urlpatterns = [
    # URL for the phone charging API
    path('charge/', ChargeAPIView.as_view(), name='charge_api'),
]