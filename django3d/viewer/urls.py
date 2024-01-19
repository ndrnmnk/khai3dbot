from django.urls import path
from . import views

urlpatterns = [
    path('demo/', views.demo, name='demo'),
    path('<int:pk>', views.ModelView.as_view(), name='view_model'),
    path('sfm/<int:pk>', views.LiteModelView.as_view(), name='view_model_sfm')
]
