
from django.urls import path

from . import views

urlpatterns = [
            # path('', views.index, name='index'),
            path('status', views.check_status, name='status'),
            path('', views.launch, name='index'),

            ]
