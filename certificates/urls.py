from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('community/', views.community, name='community'),
    path('getapp/', views.getapp, name='getapp'),
    path('certificates/generate/', views.issue_certificate, name='issue_certificate'),
    path('certificates/pdf/<str:certificate_id>/', views.generate_certificate_pdf, name='generate_certificate_pdf'),
]
