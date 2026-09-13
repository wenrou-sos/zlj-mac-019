from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import (
    DyeVat,
    Machine,
    Order,
    ProcessParameter,
    ProcessStep,
    QualityIssue,
    ReworkRecord,
)
from .serializers import (
    DyeVatDetailSerializer,
    DyeVatListSerializer,
    MachineSerializer,
    OrderDetailSerializer,
    OrderSerializer,
    ProcessParameterSerializer,
    ProcessStepSerializer,
    QualityIssueSerializer,
    ReworkRecordSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related("vats").all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        keyword = self.request.query_params.get("keyword")
        status_ = self.request.query_params.get("status")
        if keyword:
            qs = qs.filter(order_no__icontains=keyword) | qs.filter(customer__icontains=keyword)
        if status_:
            qs = qs.filter(status=status_)
        return qs


class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer

    @action(detail=False, methods=["get"])
    def board(self, request):
        """排缸看板：每个机台及其已排缸号"""
        data = []
        for m in self.get_queryset().filter(is_active=True):
            vats = m.vats.filter(status__in=["scheduled", "producing"]).order_by("planned_start")
            data.append(
                {
                    "machine": MachineSerializer(m).data,
                    "vats": DyeVatListSerializer(vats, many=True).data,
                }
            )
        return Response(data)


class DyeVatViewSet(viewsets.ModelViewSet):
    queryset = DyeVat.objects.select_related("order", "machine").prefetch_related("steps").all()

    def perform_create(self, serializer):
        """新建缸号时补齐默认工艺参数与 9 道标准工序"""
        vat = serializer.save()
        ProcessParameter.objects.create(vat=vat)
        for i, (step, _) in enumerate(ProcessStep.STEP_CHOICES):
            ProcessStep.objects.create(vat=vat, step=step, seq=i)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DyeVatDetailSerializer
        return DyeVatListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_ = self.request.query_params.get("status")
        order_id = self.request.query_params.get("order")
        if status_:
            qs = qs.filter(status=status_)
        if order_id:
            qs = qs.filter(order_id=order_id)
        return qs

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        """排缸：指定机台与计划时间，带冲突校验"""
        vat = self.get_object()
        machine_id = request.data.get("machine")
        planned_start = parse_datetime(str(request.data.get("planned_start") or ""))
        planned_end = parse_datetime(str(request.data.get("planned_end") or ""))
        if not machine_id or not planned_start or not planned_end:
            return Response({"detail": "机台、计划开始/结束时间必填"}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.is_naive(planned_start):
            planned_start = timezone.make_aware(planned_start)
        if timezone.is_naive(planned_end):
            planned_end = timezone.make_aware(planned_end)
        if planned_end <= planned_start:
            return Response({"detail": "计划结束时间必须晚于开始时间"}, status=status.HTTP_400_BAD_REQUEST)
        if not Machine.objects.filter(pk=machine_id, is_active=True).exists():
            return Response({"detail": "机台不存在或已停用"}, status=status.HTTP_400_BAD_REQUEST)
        conflict = (
            DyeVat.objects.filter(machine_id=machine_id, status__in=["scheduled", "producing"])
            .exclude(pk=vat.pk)
            .filter(planned_start__lt=planned_end, planned_end__gt=planned_start)
            .exists()
        )
        if conflict:
            return Response({"detail": "该机台在所选时间段已有排缸计划"}, status=status.HTTP_400_BAD_REQUEST)
        vat.machine_id = machine_id
        vat.planned_start = planned_start
        vat.planned_end = planned_end
        vat.status = "scheduled"
        vat.save()
        return Response(DyeVatDetailSerializer(vat).data)

    @action(detail=True, methods=["post"])
    def unschedule(self, request, pk=None):
        vat = self.get_object()
        vat.machine = None
        vat.planned_start = vat.planned_end = None
        vat.status = "unscheduled"
        vat.save()
        return Response(DyeVatDetailSerializer(vat).data)


class ProcessParameterViewSet(viewsets.ModelViewSet):
    queryset = ProcessParameter.objects.all()
    serializer_class = ProcessParameterSerializer


class ProcessStepViewSet(viewsets.ModelViewSet):
    queryset = ProcessStep.objects.select_related("vat").all()
    serializer_class = ProcessStepSerializer

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        """推进工序状态：未开始 -> 进行中 -> 已完成，自动记录时间并联动缸号状态"""
        step = self.get_object()
        now = timezone.now()
        if step.status == "not_started":
            step.status = "in_progress"
            step.start_time = now
            step.operator = request.data.get("operator", step.operator)
        elif step.status == "in_progress":
            step.status = "done"
            step.end_time = now
        elif step.status == "abnormal":
            step.status = "in_progress"
        step.save()
        vat = step.vat
        steps = list(vat.steps.all())
        if all(s.status == "done" for s in steps):
            vat.status = "completed"
            vat.actual_end = now
        elif any(s.status in ("in_progress", "done") for s in steps):
            if vat.status in ("scheduled", "unscheduled"):
                vat.status = "producing"
                vat.actual_start = vat.actual_start or now
            if step.step == "inspection" and step.status == "done":
                vat.status = "inspecting"
        vat.save()
        return Response(ProcessStepSerializer(step).data)

    @action(detail=True, methods=["post"])
    def mark_abnormal(self, request, pk=None):
        step = self.get_object()
        step.status = "abnormal"
        step.save()
        return Response(ProcessStepSerializer(step).data)


class QualityIssueViewSet(viewsets.ModelViewSet):
    queryset = QualityIssue.objects.select_related("vat", "vat__order").all()
    serializer_class = QualityIssueSerializer

    def perform_create(self, serializer):
        # 取当日最大序号 +1，删除历史单后也不会撞唯一约束
        today = timezone.now().strftime("%Y%m%d")
        last = (
            QualityIssue.objects.filter(issue_no__startswith=f"QI{today}")
            .order_by("-issue_no")
            .values_list("issue_no", flat=True)
            .first()
        )
        seq = int(last.rsplit("-", 1)[-1]) + 1 if last else 1
        serializer.save(issue_no=f"QI{today}-{seq:03d}")

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        issue = self.get_object()
        target = request.data.get("status")
        if target not in ("open", "processing", "closed"):
            return Response({"detail": "非法状态"}, status=status.HTTP_400_BAD_REQUEST)
        issue.status = target
        issue.closed_at = timezone.now() if target == "closed" else None
        issue.save()
        return Response(QualityIssueSerializer(issue).data)


class ReworkRecordViewSet(viewsets.ModelViewSet):
    queryset = ReworkRecord.objects.select_related("issue", "issue__vat").all()
    serializer_class = ReworkRecordSerializer

    def perform_create(self, serializer):
        record = serializer.save()
        issue = record.issue
        if issue.status == "open":
            issue.status = "processing"
            issue.save()

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        record = self.get_object()
        record.status = "done"
        record.result = request.data.get("result", "pass")
        record.finished_at = timezone.now()
        record.save()
        issue = record.issue
        if record.result == "pass":
            issue.status = "closed"
            issue.closed_at = timezone.now()
        issue.save()
        return Response(ReworkRecordSerializer(record).data)


@api_view(["GET"])
def dashboard(request):
    """仪表盘汇总数据"""
    orders_by_status = dict(Order.objects.values_list("status").annotate(c=Count("id")))
    vats_by_status = dict(DyeVat.objects.values_list("status").annotate(c=Count("id")))
    issues_by_type = dict(QualityIssue.objects.values_list("issue_type").annotate(c=Count("id")))
    recent_issues = QualityIssueSerializer(
        QualityIssue.objects.select_related("vat", "vat__order").order_by("-created_at")[:5], many=True
    ).data
    producing_vats = DyeVatListSerializer(
        DyeVat.objects.filter(status__in=["producing", "scheduled"]).select_related("order", "machine")[:8],
        many=True,
    ).data
    return Response(
        {
            "order_total": Order.objects.count(),
            "order_producing": orders_by_status.get("producing", 0),
            "vat_producing": vats_by_status.get("producing", 0),
            "vat_unscheduled": vats_by_status.get("unscheduled", 0),
            "issue_open": QualityIssue.objects.exclude(status="closed").count(),
            "rework_active": ReworkRecord.objects.exclude(status="done").count(),
            "total_output_kg": DyeVat.objects.filter(status="completed").aggregate(s=Sum("weight_kg"))["s"] or 0,
            "orders_by_status": orders_by_status,
            "vats_by_status": vats_by_status,
            "issues_by_type": issues_by_type,
            "recent_issues": recent_issues,
            "producing_vats": producing_vats,
        }
    )
