from rest_framework import serializers

from .models import (
    DyeVat,
    Machine,
    Order,
    ProcessParameter,
    ProcessStep,
    ProcessTemplate,
    QualityIssue,
    ReworkRecord,
    compute_schedule_warnings,
)
from .risk import order_risk_info, vat_delay_info


class ProcessTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessTemplate
        fields = "__all__"


class MachineSerializer(serializers.ModelSerializer):
    machine_type_display = serializers.CharField(source="get_machine_type_display", read_only=True)

    class Meta:
        model = Machine
        fields = "__all__"


class ProcessParameterSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True, default=None)

    class Meta:
        model = ProcessParameter
        exclude = ("vat",)


class ProcessStepSerializer(serializers.ModelSerializer):
    step_display = serializers.CharField(source="get_step_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProcessStep
        fields = "__all__"


class DyeVatListSerializer(serializers.ModelSerializer):
    order_no = serializers.CharField(source="order.order_no", read_only=True)
    customer = serializers.CharField(source="order.customer", read_only=True)
    color = serializers.CharField(source="order.color", read_only=True)
    color_no = serializers.CharField(source="order.color_no", read_only=True)
    fabric_type = serializers.CharField(source="order.fabric_type", read_only=True)
    machine_name = serializers.CharField(source="machine.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_priority = serializers.CharField(source="order.priority", read_only=True)
    order_priority_display = serializers.CharField(source="order.get_priority_display", read_only=True)
    order_delivery = serializers.DateField(source="order.delivery_date", read_only=True)
    done_steps = serializers.SerializerMethodField()
    total_steps = serializers.SerializerMethodField()
    schedule_warnings = serializers.SerializerMethodField()
    delay_info = serializers.SerializerMethodField()
    current_step = serializers.SerializerMethodField()

    class Meta:
        model = DyeVat
        fields = "__all__"

    def get_done_steps(self, obj):
        return obj.steps.filter(status="done").count()

    def get_total_steps(self, obj):
        return obj.steps.count()

    def get_schedule_warnings(self, obj):
        # 动态计算：已排缸号后续改重量/换机台都会重新提示
        if obj.status not in ("scheduled", "producing") or not obj.machine:
            return []
        return compute_schedule_warnings(obj, obj.machine)

    def get_delay_info(self, obj):
        # 动态计算：落后计划标记随工序推进/排缸调整自动刷新
        return vat_delay_info(obj)

    def get_current_step(self, obj):
        steps = list(obj.steps.all())
        for s in steps:
            if s.status == "in_progress":
                return f"{s.get_step_display()}（进行中）"
            if s.status == "abnormal":
                return f"{s.get_step_display()}（异常）"
        if steps and all(s.status == "done" for s in steps):
            return "全部完成"
        for s in steps:
            if s.status == "not_started":
                return f"待{s.get_step_display()}"
        return "—"


class DyeVatDetailSerializer(DyeVatListSerializer):
    params = ProcessParameterSerializer(read_only=True)
    steps = ProcessStepSerializer(many=True, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    vat_count = serializers.IntegerField(source="vats.count", read_only=True)
    produced_kg = serializers.SerializerMethodField()
    risk = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"

    def get_produced_kg(self, obj):
        return sum(v.weight_kg for v in obj.vats.all() if v.status == "completed")

    def get_risk(self, obj):
        # 实时计算：随排缸调整、工序推进、异常处理自动刷新
        return order_risk_info(obj)


class OrderDetailSerializer(OrderSerializer):
    vats = DyeVatListSerializer(many=True, read_only=True)


class QualityIssueSerializer(serializers.ModelSerializer):
    issue_type_display = serializers.CharField(source="get_issue_type_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    vat_no = serializers.CharField(source="vat.vat_no", read_only=True)
    order_no = serializers.CharField(source="vat.order.order_no", read_only=True)
    rework_count = serializers.IntegerField(source="reworks.count", read_only=True)

    class Meta:
        model = QualityIssue
        fields = "__all__"
        read_only_fields = ("issue_no",)


class ReworkRecordSerializer(serializers.ModelSerializer):
    rework_type_display = serializers.CharField(source="get_rework_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    result_display = serializers.CharField(source="get_result_display", read_only=True)
    issue_no = serializers.CharField(source="issue.issue_no", read_only=True)
    vat_no = serializers.CharField(source="issue.vat.vat_no", read_only=True)
    issue_type_display = serializers.CharField(source="issue.get_issue_type_display", read_only=True)

    class Meta:
        model = ReworkRecord
        fields = "__all__"
