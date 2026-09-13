"""交期与进度风险：全部实时计算，随排缸调整、工序推进、异常处理自动刷新"""

from datetime import timedelta

from django.utils import timezone

STEP_HOURS = 1.0  # 估算：单道工序平均耗时
UNSCHEDULED_HOURS = 24  # 估算：未排缸号从排产到完工的最短周期
PROGRESS_LAG_TOLERANCE = 0.15  # 时间进度超过工序进度 15% 判定落后
NEAR_DELIVERY_DAYS = 2  # 交期剩余 <= 2 天时，所有未完工缸的阻塞都计入订单风险


def _steps(vat):
    return list(vat.steps.all())


def vat_delay_info(vat, now=None):
    """缸号是否落后计划，返回 {delayed, reason}"""
    now = now or timezone.now()
    empty = {"delayed": False, "reason": ""}
    if vat.status == "completed":
        return empty
    if vat.planned_end and vat.planned_end < now:
        return {
            "delayed": True,
            "reason": f"计划 {timezone.localtime(vat.planned_end):%m-%d %H:%M} 完工，现已超期",
        }
    if (
        vat.status == "producing"
        and vat.planned_start
        and vat.planned_end
        and vat.planned_start < now < vat.planned_end
    ):
        span = (vat.planned_end - vat.planned_start).total_seconds()
        if span > 0:
            steps = _steps(vat)
            total = len(steps)
            done = sum(1 for s in steps if s.status == "done")
            time_pct = (now - vat.planned_start).total_seconds() / span
            actual_pct = done / total if total else 0
            if time_pct - actual_pct > PROGRESS_LAG_TOLERANCE:
                return {
                    "delayed": True,
                    "reason": f"时间进度 {time_pct:.0%}，工序仅完成 {actual_pct:.0%}",
                }
    return empty


def _vat_estimated_finish(vat, now):
    """按当前进度估算单缸完工时间"""
    steps = _steps(vat)
    total = len(steps) or 9
    remaining = sum(1 for s in steps if s.status != "done")
    if vat.status == "unscheduled":
        return now + timedelta(hours=UNSCHEDULED_HOURS)
    if vat.status == "producing":
        done = total - remaining
        if done and vat.actual_start:
            pace = (now - vat.actual_start) / done  # 当前节奏：每道工序耗时
            return now + pace * remaining
        return now + timedelta(hours=STEP_HOURS * remaining)
    # scheduled / inspecting
    if vat.planned_end and vat.planned_end > now:
        return vat.planned_end
    return now + timedelta(hours=STEP_HOURS * remaining)


def order_risk_info(order, now=None):
    """订单交期风险，返回 {level, reasons, estimated_finish}

    level: overdue 已拖期 / at_risk 拖期风险 / ok 正常
    原因归因为：卡在排缸 / 卡在工序 / 卡在异常返修
    """
    now = now or timezone.now()
    ok = {"level": "ok", "reasons": [], "estimated_finish": None}
    if order.status in ("completed", "shipped"):
        return ok

    today = now.date()
    vats = list(order.vats.all())
    reasons, ests = [], []
    near_delivery = (order.delivery_date - today).days <= NEAR_DELIVERY_DAYS

    if not vats and near_delivery:
        reasons.append("订单尚未分缸（卡在排缸）")

    for vat in vats:
        if vat.status == "completed":
            continue
        est = _vat_estimated_finish(vat, now)
        ests.append(est)
        # 交期尚远时不报阻塞，避免噪音；临近或已威胁交期时才列出原因
        threatens = near_delivery or est.date() > order.delivery_date
        if not threatens:
            continue
        if vat.status == "unscheduled":
            reasons.append(f"{vat.vat_no} 未排缸（卡在排缸）")
        else:
            d = vat_delay_info(vat, now)
            if d["delayed"]:
                reasons.append(f"{vat.vat_no} {d['reason']}（卡在工序）")
        open_issues = sum(1 for i in vat.issues.all() if i.status != "closed")
        active_reworks = sum(1 for i in vat.issues.all() for r in i.reworks.all() if r.status != "done")
        if open_issues or active_reworks:
            parts = []
            if open_issues:
                parts.append(f"{open_issues} 条异常未关闭")
            if active_reworks:
                parts.append(f"{active_reworks} 条返修未结案")
            reasons.append(f"{vat.vat_no} {'、'.join(parts)}（卡在异常返修）")

    estimated_finish = max(ests) if ests else None

    if order.delivery_date < today:
        return {
            "level": "overdue",
            "reasons": [f"交期 {order.delivery_date:%Y-%m-%d} 已过，订单未完工"] + reasons,
            "estimated_finish": estimated_finish,
        }
    will_late = estimated_finish and estimated_finish.date() > order.delivery_date
    if will_late or reasons:
        head = []
        if will_late:
            head.append(
                f"按当前进度预计 {timezone.localtime(estimated_finish):%m-%d %H:%M} 完工，"
                f"超过交期 {order.delivery_date:%m-%d}"
            )
        return {"level": "at_risk", "reasons": head + reasons, "estimated_finish": estimated_finish}
    return ok
