from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_resume, name='upload_resume'),
    path('match/', views.match_resume_to_job, name='match_resume_to_job'),
    path('ranking/', views.job_ranking, name='job_ranking'),
]