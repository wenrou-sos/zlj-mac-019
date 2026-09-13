from django.contrib import admin

from .models import (
    DyeVat,
    Machine,
    Order,
    ProcessParameter,
    ProcessStep,
    QualityIssue,
    ReworkRecord,
)


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    extra = 0


class ProcessParameterInline(admin.StackedInline):
    model = ProcessParameter


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_no", "customer", "fabric_type", "color", "quantity_kg", "delivery_date", "priority", "status")
    list_filter = ("status", "priority")
    search_fields = ("order_no", "customer")


@admin.register(DyeVat)
class DyeVatAdmin(admin.ModelAdmin):
    list_display = ("vat_no", "order", "machine", "weight_kg", "status", "planned_start")
    list_filter = ("status", "machine")
    search_fields = ("vat_no", "order__order_no")
    inlines = [ProcessParameterInline, ProcessStepInline]


admin.site.register(Machine)
admin.site.register(ProcessStep)
admin.site.register(QualityIssue)
admin.site.register(ReworkRecord)
