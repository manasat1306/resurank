from django.urls import path
from . import views

app_name = 'candidate'

urlpatterns = [
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/apply/', views.apply, name='apply'),
]