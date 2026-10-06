from django.urls import path
from . import views,job_views

urlpatterns = [
    path('', views.upload_resume, name='upload_resume'),
    path('match/', views.match_resume_to_job, name='match_resume_to_job'),
    path('ranking/', views.job_ranking, name='job_ranking'),
    path('signup/', views.signup, name='signup'),
    path('jobs/', job_views.job_list, name='job_list'),
    path('jobs/new/', job_views.job_create, name='job_create'),
    path('jobs/<int:pk>/', job_views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', job_views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/publish/', job_views.job_publish, name='job_publish'),
    path('jobs/<int:pk>/close/', job_views.job_close, name='job_close'),
        path('jobs/<int:pk>/applicants/', job_views.job_applicants, name='job_applicants'),
]
    