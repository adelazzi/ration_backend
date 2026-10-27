from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('projects/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('config/', views.config_view, name='config'),
    path('config/materials/add/', views.material_add_view, name='material_add'),
    path('config/prices/add/', views.price_add_view, name='price_add'),
    path('config/prices/<int:pk>/review/', views.price_review_view, name='price_review'),
    path('config/mixes/new/', views.mix_edit_view, name='mix_new'),
    path('config/mixes/<int:pk>/', views.mix_edit_view, name='mix_edit'),
]
