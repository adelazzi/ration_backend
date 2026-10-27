from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('projects/', views.project_list_view, name='project_list'),
    path('projects/new/', views.project_new_view, name='project_new'),
    path('projects/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit_view, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete_view, name='project_delete'),
    path('projects/<int:pk>/blocks/<int:block_pk>/mix/', views.project_choose_mix_view, name='project_choose_mix'),
    path('projects/<int:pk>/prices/add/', views.project_price_add_view, name='project_price_add'),
    path('config/', views.config_view, name='config'),
    path('config/materials/add/', views.material_add_view, name='material_add'),
    path('config/materials/<int:pk>/', views.material_edit_view, name='material_edit'),
    path('config/materials/<int:pk>/delete/', views.material_delete_view, name='material_delete'),
    path('config/prices/add/', views.price_add_view, name='price_add'),
    path('config/prices/<int:pk>/review/', views.price_review_view, name='price_review'),
    path('config/prices/<int:pk>/delete/', views.price_delete_view, name='price_delete'),
    path('config/mixes/new/', views.mix_edit_view, name='mix_new'),
    path('config/mixes/<int:pk>/', views.mix_edit_view, name='mix_edit'),
    path('config/mixes/<int:pk>/delete/', views.mix_delete_view, name='mix_delete'),
]
