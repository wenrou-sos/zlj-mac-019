from django.db import models


class Order(models.Model):
    """生产订单"""

    STATUS_CHOICES = [
        ("pending", "待生产"),
        ("producing", "生产中"),
        ("completed", "已完成"),
        ("shipped", "已出货"),
    ]
    PRIORITY_CHOICES = [
        ("normal", "普通"),
        ("urgent", "加急"),
        ("critical", "特急"),
    ]

    order_no = models.CharField("订单号", max_length=50, unique=True)
    customer = models.CharField("客户", max_length=100)
    fabric_type = models.CharField("布种", max_length=100)
    composition = models.CharField("成分", max_length=100, blank=True)
    color = models.CharField("颜色", max_length=50)
    color_no = models.CharField("色号", max_length=50, blank=True)
    quantity_kg = models.DecimalField("订单数量(kg)", max_digits=10, decimal_places=1)
    delivery_date = models.DateField("交期")
    priority = models.CharField("优先级", max_length=10, choices=PRIORITY_CHOICES, default="normal")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    remark = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_no} {self.customer}"


class Machine(models.Model):
    """染缸机台"""

    TYPE_CHOICES = [
        ("overflow", "溢流染色机"),
        ("jet", "喷射染色机"),
        ("jigger", "卷染机"),
        ("airflow", "气流染色机"),
    ]

    name = models.CharField("机台名称", max_length=50)
    machine_type = models.CharField("机型", max_length=20, choices=TYPE_CHOICES, default="overflow")
    capacity_kg = models.PositiveIntegerField("容量(kg)", default=500)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class DyeVat(models.Model):
    """生产缸号"""

    STATUS_CHOICES = [
        ("unscheduled", "待排缸"),
        ("scheduled", "已排缸"),
        ("producing", "生产中"),
        ("inspecting", "待检验"),
        ("completed", "已完成"),
    ]

    vat_no = models.CharField("缸号", max_length=50, unique=True)
    order = models.ForeignKey(Order, verbose_name="订单", related_name="vats", on_delete=models.CASCADE)
    machine = models.ForeignKey(
        Machine, verbose_name="机台", related_name="vats", null=True, blank=True, on_delete=models.SET_NULL
    )
    weight_kg = models.DecimalField("本缸重量(kg)", max_digits=10, decimal_places=1)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="unscheduled")
    planned_start = models.DateTimeField("计划开始", null=True, blank=True)
    planned_end = models.DateTimeField("计划结束", null=True, blank=True)
    actual_start = models.DateTimeField("实际开始", null=True, blank=True)
    actual_end = models.DateTimeField("实际结束", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["vat_no"]

    def __str__(self):
        return self.vat_no


# 机型-布种适配规则：(机型, 不适配的布种关键词, 原因)
MACHINE_FABRIC_RULES = [
    ("jigger", ["针织"], "卷染机不适合针织布（易卷边、拉伸变形）"),
    ("airflow", ["梭织", "府绸", "塔丝隆", "斜纹"], "气流染色机不适合梭织类布种"),
]


def machine_suitability(machine, fabric_type):
    """返回 (是否适配, 原因)"""
    for mtype, keywords, reason in MACHINE_FABRIC_RULES:
        if machine.machine_type == mtype and any(k in (fabric_type or "") for k in keywords):
            return False, f"机型不适配：{reason}"
    return True, ""


def compute_schedule_warnings(vat, machine):
    """排缸校验：超容 + 机型适配，返回警告文案列表"""
    warnings = []
    if machine is None:
        return warnings
    if vat.weight_kg > machine.capacity_kg:
        warnings.append(f"超容：本缸 {vat.weight_kg}kg 超过机台容量 {machine.capacity_kg}kg")
    ok, reason = machine_suitability(machine, vat.order.fabric_type)
    if not ok:
        warnings.append(reason)
    return warnings


class ProcessTemplate(models.Model):
    """成熟工艺模板：按布种+色号（或客户确认样）沉淀的配方"""

    name = models.CharField("模板名称", max_length=100, unique=True)
    fabric_type = models.CharField("适用布种", max_length=100)
    color_no = models.CharField("色号", max_length=50, blank=True)
    color = models.CharField("颜色", max_length=50, blank=True)
    customer = models.CharField("客户确认样", max_length=100, blank=True)
    bath_ratio = models.CharField("浴比", max_length=20, default="1:10")
    dye_temp = models.DecimalField("染色温度(℃)", max_digits=5, decimal_places=1, default=98.0)
    dye_time = models.PositiveIntegerField("保温时间(min)", default=40)
    ph_value = models.DecimalField("pH值", max_digits=3, decimal_places=1, default=7.0)
    heating_rate = models.DecimalField("升温速率(℃/min)", max_digits=3, decimal_places=1, default=2.0)
    dyes = models.JSONField("染料配方", default=list, blank=True)
    auxiliaries = models.JSONField("助剂", default=list, blank=True)
    note = models.TextField("工艺备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


# 模板/缸号工艺参数之间需要整套拷贝的字段
PARAM_FIELDS = ["bath_ratio", "dye_temp", "dye_time", "ph_value", "heating_rate", "dyes", "auxiliaries", "note"]


class ProcessParameter(models.Model):
    """缸号对应的染色工艺参数"""

    vat = models.OneToOneField(DyeVat, verbose_name="缸号", related_name="params", on_delete=models.CASCADE)
    template = models.ForeignKey(
        ProcessTemplate,
        verbose_name="执行模板",
        related_name="vat_params",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="套用的模板（值为快照，模板后续改动不影响本缸）",
    )
    bath_ratio = models.CharField("浴比", max_length=20, default="1:10")
    dye_temp = models.DecimalField("染色温度(℃)", max_digits=5, decimal_places=1, default=98.0)
    dye_time = models.PositiveIntegerField("保温时间(min)", default=40)
    ph_value = models.DecimalField("pH值", max_digits=3, decimal_places=1, default=7.0)
    heating_rate = models.DecimalField("升温速率(℃/min)", max_digits=3, decimal_places=1, default=2.0)
    dyes = models.JSONField("染料配方", default=list, blank=True, help_text='[{"name":"分散红","pct":1.2}]')
    auxiliaries = models.JSONField("助剂", default=list, blank=True, help_text='[{"name":"匀染剂","gpl":1.0}]')
    note = models.TextField("工艺备注", blank=True)

    def __str__(self):
        return f"{self.vat.vat_no} 工艺参数"


class ProcessStep(models.Model):
    """各缸号的工序进度"""

    STEP_CHOICES = [
        ("pretreatment", "前处理"),
        ("dyeing", "染色"),
        ("soaping", "皂洗"),
        ("fixing", "固色"),
        ("dewatering", "脱水"),
        ("drying", "烘干"),
        ("setting", "定型"),
        ("inspection", "检验"),
        ("packing", "包装"),
    ]
    STATUS_CHOICES = [
        ("not_started", "未开始"),
        ("in_progress", "进行中"),
        ("done", "已完成"),
        ("abnormal", "异常"),
    ]

    vat = models.ForeignKey(DyeVat, verbose_name="缸号", related_name="steps", on_delete=models.CASCADE)
    step = models.CharField("工序", max_length=20, choices=STEP_CHOICES)
    seq = models.PositiveSmallIntegerField("顺序", default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="not_started")
    operator = models.CharField("操作工", max_length=50, blank=True)
    start_time = models.DateTimeField("开始时间", null=True, blank=True)
    end_time = models.DateTimeField("结束时间", null=True, blank=True)

    class Meta:
        ordering = ["vat", "seq"]
        unique_together = ("vat", "step")

    def __str__(self):
        return f"{self.vat.vat_no}-{self.get_step_display()}"


class QualityIssue(models.Model):
    """质量异常上报"""

    TYPE_CHOICES = [
        ("color_diff", "色差"),
        ("color_flower", "色花"),
        ("stain", "沾污"),
        ("fastness", "色牢度不合格"),
        ("defect", "布面疵点"),
        ("strength", "强力不足"),
        ("other", "其他"),
    ]
    SEVERITY_CHOICES = [
        ("minor", "轻微"),
        ("major", "一般"),
        ("critical", "严重"),
    ]
    STATUS_CHOICES = [
        ("open", "待处理"),
        ("processing", "处理中"),
        ("closed", "已关闭"),
    ]

    issue_no = models.CharField("异常单号", max_length=50, unique=True)
    vat = models.ForeignKey(DyeVat, verbose_name="缸号", related_name="issues", on_delete=models.CASCADE)
    issue_type = models.CharField("异常类型", max_length=20, choices=TYPE_CHOICES)
    severity = models.CharField("严重程度", max_length=10, choices=SEVERITY_CHOICES, default="major")
    description = models.TextField("异常描述")
    reporter = models.CharField("上报人", max_length=50)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField("上报时间", auto_now_add=True)
    closed_at = models.DateTimeField("关闭时间", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.issue_no


class ReworkRecord(models.Model):
    """返修跟踪"""

    TYPE_CHOICES = [
        ("redye", "复染"),
        ("strip_redye", "剥色重染"),
        ("resetting", "回修定型"),
        ("rewash", "回洗"),
        ("other", "其他"),
    ]
    STATUS_CHOICES = [
        ("pending", "待处理"),
        ("processing", "进行中"),
        ("done", "已完成"),
    ]
    RESULT_CHOICES = [
        ("", "待定"),
        ("pass", "合格"),
        ("fail", "不合格"),
    ]

    issue = models.ForeignKey(QualityIssue, verbose_name="关联异常", related_name="reworks", on_delete=models.CASCADE)
    rework_type = models.CharField("返修方式", max_length=20, choices=TYPE_CHOICES, default="redye")
    plan = models.TextField("处理方案")
    operator = models.CharField("负责人", max_length=50, blank=True)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    result = models.CharField("返修结果", max_length=10, choices=RESULT_CHOICES, blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"返修-{self.issue.issue_no}"
