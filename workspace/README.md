# 纺织印染车间生产管理系统

覆盖印染车间核心业务的 MES 系统：订单管理、缸号拆分、工艺参数、工序进度、排缸安排、质量异常上报与返修跟踪。

## 技术栈

- **前端**：Vue 3 + Vite + Element Plus + ECharts
- **后端**：Django 5 + Django REST Framework
- **数据库**：PostgreSQL 18（本环境通过 conda-forge 二进制免 root 运行，位于 `pgenv/`）

## 目录结构

```
backend/            Django 项目
  config/           项目配置（settings 中 DATABASES 支持 PG* 环境变量覆盖）
  production/       业务应用
    models.py       Order / Machine / DyeVat / ProcessParameter / ProcessStep / QualityIssue / ReworkRecord
    views.py        REST API + 排缸冲突校验 + 工序状态联动 + 仪表盘汇总
    management/commands/seed.py   样例数据
frontend/           Vue 3 前端
  src/views/        仪表盘 / 订单 / 订单详情 / 排缸 / 工序进度 / 质量异常 / 返修跟踪
  src/components/VatPanel.vue     缸号面板（工艺参数编辑 + 工序推进，两页共用）
start.sh            一键启动脚本
```

## 快速启动

```bash
./start.sh --seed     # 首次运行：初始化数据库并写入样例数据
./start.sh            # 之后运行
```

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/ （如 `/api/orders/`、`/api/dashboard/`）
- Django Admin：http://localhost:8000/admin/

## 核心功能

| 模块 | 说明 |
| --- | --- |
| 订单管理 | 订单增改查、按单号/客户/状态筛选，点击进入详情 |
| 缸号管理 | 订单拆分为多个缸号，记录重量、机台、计划/实际时间 |
| 工艺参数 | 每缸一套：浴比、温度、保温时间、pH、升温速率、染料配方、助剂 |
| 工序进度 | 9 道标准工序（前处理→染色→皂洗→固色→脱水→烘干→定型→检验→包装），逐步推进并自动联动缸号状态 |
| 排缸安排 | 待排缸列表 + 机台看板，选择机台与计划时间，**自动校验同机台时间冲突** |
| 质量异常 | 按缸号上报（色差/色花/沾污/牢度等），状态流转：待处理→处理中→已关闭 |
| 返修跟踪 | 关联异常发起返修（复染/剥色重染/回修定型/回洗），合格结案后自动关闭异常 |

## 主要 API

```
GET  /api/dashboard/                仪表盘汇总
GET/POST/PUT  /api/orders/          订单
GET/POST      /api/vats/            缸号
POST /api/vats/{id}/schedule/       排缸（带冲突校验）
POST /api/vats/{id}/unschedule/     取消排缸
GET/PUT /api/params/                工艺参数
POST /api/steps/{id}/advance/       推进工序
POST /api/steps/{id}/mark_abnormal/ 标记工序异常
GET/POST /api/issues/               质量异常
POST /api/issues/{id}/transition/   异常状态流转
GET/POST /api/reworks/              返修单
POST /api/reworks/{id}/finish/      返修结案（合格则自动关闭异常）
GET  /api/machines/board/           排缸看板
```

## 样例数据

`python manage.py seed` 生成：8 张订单（华纺集团、江南服饰等）、6 台染缸机台、18 个缸号（含待排缸/已排缸/生产中/已完成各状态）、162 条工序记录、5 条质量异常、4 条返修单，可直接体验完整业务流程。
