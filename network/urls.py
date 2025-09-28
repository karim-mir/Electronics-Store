from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NetworkNodeViewSet

router = DefaultRouter()
router.register(r"network-nodes", NetworkNodeViewSet, basename="networknode")

urlpatterns = [
    path("", include(router.urls)),
]
