from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Создаем схему для Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Electronics Store API",
        default_version='v1',
        description="API для управления сетью продаж электроники",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="karimov.nazir00@yandex.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('network.urls')),

    # Документация API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
