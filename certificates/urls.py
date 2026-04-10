from django.urls import path
from . import views, enhanced_views

urlpatterns = [
    # Enhanced SSI URLs (new homepage)
    path('', enhanced_views.index, name='home'),
    path('ssi/', enhanced_views.ssi_dashboard, name='ssi_dashboard'),
    path('ssi/verify/', enhanced_views.verify_certificate, name='verify_certificate'),
    path('ssi/create/', enhanced_views.create_identity, name='create_identity'),
    path('services/match/', enhanced_views.service_matching, name='service_matching'),
    path('zk/proof/', enhanced_views.generate_zk_proof, name='generate_zk_proof'),
    path('services/request/', enhanced_views.request_service, name='request_service'),
    path('eligibility/verify/', enhanced_views.verify_eligibility, name='verify_eligibility'),
    path('eligibility/verify/page/', enhanced_views.verify_eligibility, name='verify_eligibility_page'),
    
    # API endpoints
    path('api/services/<int:service_type>/', enhanced_views.api_service_eligibility, name='api_service_eligibility'),
    path('api/docs/', enhanced_views.api_documentation, name='api_documentation'),
    
    # Legacy URLs (original system)
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('getapp/', views.getapp, name='getapp'),
    path('certificates/generate/', views.issue_certificate, name='issue_certificate'),
    path('certificates/pdf/<str:certificate_id>/', views.generate_certificate_pdf, name='generate_certificate_pdf'),
]
