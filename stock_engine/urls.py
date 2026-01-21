from django.contrib import admin
from django.urls import path, include  # 'include' zaroori hai

urlpatterns = [
    path('admin/', admin.site.urls),
    
   
    path('analytics/', include('analytics.urls')), 
]