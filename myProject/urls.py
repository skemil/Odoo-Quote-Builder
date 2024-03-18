from django.contrib import admin
from django.urls import path
from webflow_integration import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('easytex/', views.show_index, name='show_index'),
    path('process-form/', views.process_form, name='process_form'),
]
