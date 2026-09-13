"""生成纺织印染车间样例数据：python manage.py seed"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from production.models import (
    DyeVat,
    Machine,
    Order,
    ProcessParameter,
    ProcessStep,
    QualityIssue,
    ReworkRecord,
)

STEPS = [s for s, _ in ProcessStep.STEP_CHOICES]

MACHINES = [
    ("1#溢流染缸", "overflow", 500),
    ("2#溢流染缸", "overflow", 500),
    ("3#喷射染缸", "jet", 800),
    ("4#喷射染缸", "jet", 800),
    ("5#气流染缸", "airflow", 300),
    ("6#卷染机", "jigger", 200),
]

ORDERS = [
    # 订单号, 客户, 布种, 成分, 颜色, 色号, 数量, 交期(天后), 优先级, 状态
    ("SO20260801-001", "华纺集团", "全棉针织汗布", "100%棉", "藏青", "N-2105", 3200, 12, "urgent", "producing"),
    ("SO20260803-002", "江南服饰", "涤纶梭织春亚纺", "100%涤纶", "宝蓝", "B-3318", 2500, 18, "normal", "producing"),
    ("SO20260805-003", "粤港纺织", "涤棉混纺府绸", "T/C 65/35", "米白", "W-1020", 1800, 9, "critical", "producing"),
    ("SO20260808-004", "铭远家纺", "全棉斜纹布", "100%棉", "卡其", "K-5520", 4200, 25, "normal", "producing"),
    ("SO20260810-005", "蓝海户外", "尼龙塔丝隆", "100%尼龙", "墨绿", "G-7712", 1500, 15, "urgent", "producing"),
    ("SO20260812-006", "晨曦童装", "全棉双面布", "100%棉", "粉红", "P-0930", 900, 20, "normal", "pending"),
    ("SO20260815-007", "苏绣丝绸", "人棉富春纺", "100%粘胶", "酒红", "R-4406", 1200, 30, "normal", "pending"),
    ("SO20260720-008", "华纺集团", "全棉针织汗布", "100%棉", "黑色", "BK-001", 2800, -6, "normal", "completed"),
]

# 每单的缸号拆分: (缸重kg, 机台idx或None, 状态, 计划开始(相对今天小时), 计划时长h, 已完成工序数)
VATS = {
    "SO20260801-001": [
        (480, 0, "completed", -96, 10, 9),
        (500, 0, "producing", -24, 12, 5),
        (450, 1, "producing", -12, 12, 3),
        (500, 1, "scheduled", 20, 12, 0),
        (470, None, "unscheduled", None, None, 0),
    ],
    "SO20260803-002": [
        (760, 2, "producing", -36, 14, 6),
        (780, 2, "scheduled", 8, 14, 0),
        (750, None, "unscheduled", None, None, 0),
    ],
    "SO20260805-003": [
        (600, 3, "producing", -8, 10, 2),
        (620, 3, "scheduled", 14, 10, 0),
        (580, None, "unscheduled", None, None, 0),
    ],
    "SO20260808-004": [
        (500, 4, "completed", -120, 10, 9),
        (500, 4, "producing", -30, 10, 4),
        (480, None, "unscheduled", None, None, 0),
    ],
    "SO20260810-005": [
        (280, 4, "producing", -6, 8, 1),
        (300, 5, "scheduled", 26, 8, 0),
    ],
    "SO20260720-008": [
        (500, 0, "completed", -240, 10, 9),
        (500, 1, "completed", -228, 10, 9),
    ],
}

PARAMS = {
    "藏青": {"bath_ratio": "1:10", "dye_temp": 98, "dye_time": 50, "ph_value": 6.5, "heating_rate": 1.5,
             "dyes": [{"name": "活性藏青B-GD", "pct": 4.2}, {"name": "活性红3BS", "pct": 0.35}],
             "auxiliaries": [{"name": "元明粉", "gpl": 60}, {"name": "纯碱", "gpl": 20}, {"name": "匀染剂", "gpl": 1.0}]},
    "宝蓝": {"bath_ratio": "1:8", "dye_temp": 130, "dye_time": 40, "ph_value": 5.0, "heating_rate": 2.0,
             "dyes": [{"name": "分散蓝2BLN", "pct": 2.8}, {"name": "分散红玉S-5BL", "pct": 0.12}],
             "auxiliaries": [{"name": "冰醋酸", "gpl": 0.5}, {"name": "高温匀染剂", "gpl": 1.2}]},
    "米白": {"bath_ratio": "1:10", "dye_temp": 130, "dye_time": 30, "ph_value": 5.5, "heating_rate": 2.0,
             "dyes": [{"name": "分散黄E-3G", "pct": 0.08}, {"name": "分散红E-4B", "pct": 0.02}],
             "auxiliaries": [{"name": "冰醋酸", "gpl": 0.4}, {"name": "分散剂", "gpl": 0.8}]},
    "卡其": {"bath_ratio": "1:12", "dye_temp": 98, "dye_time": 60, "ph_value": 7.0, "heating_rate": 1.5,
             "dyes": [{"name": "活性黄3RS", "pct": 1.6}, {"name": "活性红3BS", "pct": 0.45}, {"name": "活性蓝BRF", "pct": 0.3}],
             "auxiliaries": [{"name": "元明粉", "gpl": 50}, {"name": "纯碱", "gpl": 15}]},
    "墨绿": {"bath_ratio": "1:8", "dye_temp": 100, "dye_time": 45, "ph_value": 6.0, "heating_rate": 1.8,
             "dyes": [{"name": "酸性绿B", "pct": 2.1}, {"name": "酸性黄2G", "pct": 0.6}],
             "auxiliaries": [{"name": "硫酸铵", "gpl": 3.0}, {"name": "匀染剂", "gpl": 1.0}]},
    "黑色": {"bath_ratio": "1:10", "dye_temp": 98, "dye_time": 60, "ph_value": 6.8, "heating_rate": 1.5,
             "dyes": [{"name": "活性黑KN-B", "pct": 5.5}],
             "auxiliaries": [{"name": "元明粉", "gpl": 80}, {"name": "纯碱", "gpl": 25}]},
}

ISSUES = [
    # 缸序号(全局), 类型, 严重度, 描述, 上报人, 状态, 返修(方式,方案,负责人,状态,结果)
    (2, "color_diff", "major", "对样偏红光，△E=1.8 超出客户允差1.0", "王品检", "processing",
     ("redye", "降温至80℃追加活性红3BS 0.05%复染校正", "李师傅", "processing", "")),
    (4, "color_flower", "critical", "布面出现条花，疑似升温过快导致染料聚集", "张挡车", "processing",
     ("strip_redye", "保险粉剥色后按1.0℃/min升温重染", "李师傅", "pending", "")),
    (6, "stain", "minor", "布头约2米有轻微油渍沾污", "王品检", "closed",
     ("rewash", "去油剂2g/L 80℃回洗20分钟", "陈组长", "done", "pass")),
    (9, "fastness", "major", "皂洗牢度3级，客户要求4级", "赵化验", "open", None),
    (12, "defect", "minor", "定型后布边针孔过大", "刘定型", "processing",
     ("resetting", "调整针板张力回修定型", "刘定型", "done", "pass")),
]


class Command(BaseCommand):
    help = "生成样例订单、缸号、工艺参数、工序进度、质量异常与返修数据"

    def handle(self, *args, **options):
        Order.objects.all().delete()
        Machine.objects.all().delete()

        machines = [Machine.objects.create(name=n, machine_type=t, capacity_kg=c) for n, t, c in MACHINES]

        now = timezone.now()
        vat_seq = 0
        all_vats = []
        for no, customer, fabric, comp, color, color_no, qty, days, prio, st in ORDERS:
            order = Order.objects.create(
                order_no=no, customer=customer, fabric_type=fabric, composition=comp,
                color=color, color_no=color_no, quantity_kg=qty,
                delivery_date=(now + timedelta(days=days)).date(), priority=prio, status=st,
            )
            for weight, mi, vst, start_h, dur_h, done_steps in VATS.get(no, []):
                vat_seq += 1
                planned_start = now + timedelta(hours=start_h) if start_h is not None else None
                planned_end = planned_start + timedelta(hours=dur_h) if planned_start else None
                vat = DyeVat.objects.create(
                    vat_no=f"VAT{now:%Y%m}-{vat_seq:03d}",
                    order=order, machine=machines[mi] if mi is not None else None,
                    weight_kg=weight, status=vst,
                    planned_start=planned_start, planned_end=planned_end,
                    actual_start=planned_start if vst in ("producing", "completed") else None,
                    actual_end=planned_end if vst == "completed" else None,
                )
                all_vats.append(vat)
                p = PARAMS.get(color)
                if p:
                    ProcessParameter.objects.create(vat=vat, note="按客户确认样工艺执行", **p)
                for i, step in enumerate(STEPS):
                    if i < done_steps:
                        sst = "done"
                        stime = planned_start + timedelta(hours=i) if planned_start else None
                        etime = stime + timedelta(minutes=50) if stime else None
                    elif i == done_steps and vst == "producing":
                        sst, stime, etime = "in_progress", planned_start + timedelta(hours=i) if planned_start else None, None
                    else:
                        sst, stime, etime = "not_started", None, None
                    ProcessStep.objects.create(
                        vat=vat, step=step, seq=i, status=sst,
                        operator="张挡车" if sst != "not_started" else "",
                        start_time=stime, end_time=etime,
                    )

        issue_seq = 0
        for vat_idx, itype, sev, desc, reporter, ist, rework in ISSUES:
            if vat_idx >= len(all_vats):
                continue
            issue_seq += 1
            issue = QualityIssue.objects.create(
                issue_no=f"QI{now:%Y%m%d}-{issue_seq:03d}",
                vat=all_vats[vat_idx], issue_type=itype, severity=sev,
                description=desc, reporter=reporter, status=ist,
                closed_at=now if ist == "closed" else None,
            )
            if rework:
                rtype, plan, operator, rst, result = rework
                ReworkRecord.objects.create(
                    issue=issue, rework_type=rtype, plan=plan, operator=operator,
                    status=rst, result=result,
                    finished_at=now if rst == "done" else None,
                )

        self.stdout.write(self.style.SUCCESS(
            f"样例数据完成：{Order.objects.count()} 订单 / {DyeVat.objects.count()} 缸号 / "
            f"{ProcessStep.objects.count()} 工序 / {QualityIssue.objects.count()} 异常 / "
            f"{ReworkRecord.objects.count()} 返修"
        ))
