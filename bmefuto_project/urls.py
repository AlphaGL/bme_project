from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os
from core.views import custom_404, custom_500, custom_403

urlpatterns = [
    path('ibeawuchi242', admin.site.urls),
    path('', include('core.urls')),
        # PWA URLs
    path('manifest.json', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static'),
        'path': 'manifest.json'
    }, name='manifest'),
    
    path('service-worker.js', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static/js'),
        'path': 'service-worker.js'
    }, name='service-worker'),
]


handler404 = 'core.views.custom_404'
handler403 = 'core.views.custom_403'
handler500 = 'core.views.custom_500'

if settings.DEBUG:
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Serve static files - Django will automatically look in STATICFILES_DIRS
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()