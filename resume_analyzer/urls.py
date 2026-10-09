from django.urls import path
from django.views.generic import RedirectView
from . import views, job_views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='job_list', permanent=False), name='home'),
    path('signup/', views.signup, name='signup'),
    path('jobs/', job_views.job_list, name='job_list'),
    path('jobs/new/', job_views.job_create, name='job_create'),
    path('jobs/<int:pk>/', job_views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', job_views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/publish/', job_views.job_publish, name='job_publish'),
    path('jobs/<int:pk>/close/', job_views.job_close, name='job_close'),
    path('jobs/<int:pk>/applicants/', job_views.job_applicants, name='job_applicants'),
    path('jobs/<int:pk>/applicants/<int:app_id>/', job_views.candidate_analysis, name='candidate_analysis'),
    path('jobs/<int:pk>/applicants/<int:app_id>/status/', job_views.application_set_status, name='application_set_status'),
    path('jobs/<int:pk>/compare/', job_views.compare_candidates, name='compare_candidates'),
    path('compare/', job_views.compare_picker, name='compare_picker'),    
    path('analyze/', job_views.analyze_resume, name='analyze_resume'),
    path('analytics/', job_views.analytics, name='analytics'),
]