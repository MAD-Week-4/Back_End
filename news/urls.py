from django.urls import path
from .views import get_news

urlpatterns = [
    path('news/', get_news, name='get_news'),
]