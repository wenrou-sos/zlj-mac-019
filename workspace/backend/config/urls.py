from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from production import views

router = DefaultRouter()
router.register("orders", views.OrderViewSet)
router.register("machines", views.MachineViewSet)
router.register("vats", views.DyeVatViewSet)
router.register("params", views.ProcessParameterViewSet)
router.register("steps", views.ProcessStepViewSet)
router.register("issues", views.QualityIssueViewSet)
router.register("reworks", views.ReworkRecordViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/dashboard/", views.dashboard),
]
