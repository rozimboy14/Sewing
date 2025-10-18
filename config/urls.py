
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('production/',include("production.urls")),
    path('sewing/',include("sewing.urls")),
    path('stock/',include('stock.urls')),
    path('packaging/',include('packaging.urls')),
    path('users/',include('users.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


