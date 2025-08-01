from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework import permissions

from rest_framework.authentication import SessionAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="B2B API",
        default_version='v1',
        description="API Documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('B2B_shop.urls')),
    path('api-token-auth/', views.obtain_auth_token),
   #  path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),


    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]
