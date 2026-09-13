from rest_framework import serializers

from .models import (
    DyeVat,
    Machine,
    Order,
    ProcessParameter,
    ProcessStep,
    QualityIssue,
    ReworkRecord,
)


class MachineSerializer(serializers.ModelSerializer):
    machine_type_display = serializers.CharField(source="get_machine_type_display", read_only=True)

    class Meta:
        model = Machine
        fields = "__all__"


class ProcessParameterSerializer(serializers.ModelSerializer):
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
    machine_name = serializers.CharField(source="machine.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    done_steps = serializers.SerializerMethodField()
    total_steps = serializers.SerializerMethodField()

    class Meta:
        model = DyeVat
        fields = "__all__"

    def get_done_steps(self, obj):
        return obj.steps.filter(status="done").count()

    def get_total_steps(self, obj):
        return obj.steps.count()


class DyeVatDetailSerializer(DyeVatListSerializer):
    params = ProcessParameterSerializer(read_only=True)
    steps = ProcessStepSerializer(many=True, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    vat_count = serializers.IntegerField(source="vats.count", read_only=True)
    produced_kg = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"

    def get_produced_kg(self, obj):
        return sum(v.weight_kg for v in obj.vats.all() if v.status == "completed")


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
