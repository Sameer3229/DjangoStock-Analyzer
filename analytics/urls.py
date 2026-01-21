from django.urls import path
from .views import company_dashboard

urlpatterns = [
    # Yahan 'analytics/' dobara nahi likhna, wo step 1 se aa raha hai
    path('dashboard/<str:ticker_symbol>/', company_dashboard, name='dashboard'),
]