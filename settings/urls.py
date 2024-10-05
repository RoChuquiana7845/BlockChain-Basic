from django.contrib import admin
from django.urls import path, include
from student.views import BlockchainFillRegistersView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/blockchain/fill-registers/', BlockchainFillRegistersView.as_view(), name='blockchain_fill_registers'),
]
