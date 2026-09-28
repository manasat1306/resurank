from django.urls import path
from . import views,job_views

urlpatterns = [
    path('', views.upload_resume, name='upload_resume'),
    path('match/', views.match_resume_to_job, name='match_resume_to_job'),
    path('ranking/', views.job_ranking, name='job_ranking'),
    path('signup/', views.signup, name='signup'),
    path('jobs/', job_views.job_list, name='job_list'),
]