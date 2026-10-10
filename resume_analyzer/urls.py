from django.urls import path
from django.views.generic import RedirectView
from . import views, job_views

urlpatterns = [
    path('', job_views.landing, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', job_views.dashboard, name='dashboard'),
    path('jobs/', job_views.job_list, name='job_list'),
    path('jobs/new/', job_views.job_create, name='job_create'),
    path('jobs/<int:pk>/', job_views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', job_views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/publish/', job_views.job_publish, name='job_publish'),
    path('jobs/<int:pk>/close/', job_views.job_close, name='job_close'),
    path('jobs/<int:pk>/applicants/', job_views.job_applicants, name='job_applicants'),
    path('jobs/<int:pk>/applicants/<int:app_id>/', job_views.candidate_analysis, name='candidate_analysis'),
    path('jobs/<int:pk>/applicants/<int:app_id>/resume/', job_views.resume_view, name='resume_view'),
    path('jobs/<int:pk>/applicants/<int:app_id>/status/', job_views.application_set_status, name='application_set_status'),
    path('jobs/<int:pk>/compare/', job_views.compare_candidates, name='compare_candidates'),
    path('compare/', job_views.compare_picker, name='compare_picker'),    
    path('applicants/', job_views.all_applicants, name='all_applicants'),
    path('analyze/', job_views.analyze_resume, name='analyze_resume'),
    path('analytics/', job_views.analytics, name='analytics'),
    path('settings/', job_views.account_settings, name='account_settings'),
    path('help/', job_views.help_page, name='help'),
    path('plans/', job_views.plans_page, name='plans'),
    path('plans/switch/', job_views.switch_plan, name='switch_plan'),
    path('plans/checkout/', job_views.checkout_page, name='checkout'),
        
]