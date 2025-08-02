from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.CreateSellerAPIView.as_view(), name='charge_api'),
    path('credit-request/', views.CreditRequestAPIView.as_view(), name='charge_api'),
    path('transactions/', views.TransactionsAPIView.as_view(), name='charge_api'),
    path('charge/', views.ChargeAPIView.as_view(), name='charge_api'),
]