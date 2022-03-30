from django.conf.urls.static import static
from django.shortcuts import redirect
from django.conf import settings
from django.urls import path
from . import views


def admin(request):
    return redirect('admin/')


urlpatterns = [
    path('update', views.update, name='update'),
    path('updateJourney', views.journey, name='update_journey_default'),
    path('updateJourney/<str:date>', views.journey, name='update_journey'),
    path('', admin)
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
