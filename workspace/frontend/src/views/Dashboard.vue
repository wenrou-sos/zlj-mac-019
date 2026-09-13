<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col :span="4" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ c.label }}</div>
          <div class="stat-num" :style="{ color: c.color }">{{ c.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <el-card shadow="never" header="订单状态分布">
          <div ref="orderChart" style="height: 260px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" header="缸号状态分布">
          <div ref="vatChart" style="height: 260px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" header="质量异常类型分布">
          <div ref="issueChart" style="height: 260px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <el-card shadow="never" header="在产 / 已排缸号">
          <el-table :data="data.producing_vats" size="small">
            <el-table-column prop="vat_no" label="缸号" width="130" />
            <el-table-column prop="order_no" label="订单号" width="140" />
            <el-table-column prop="color" label="颜色" width="80" />
            <el-table-column prop="machine_name" label="机台" width="110">
              <template #default="{ row }">{{ row.machine_name || '—' }}</template>
            </el-table-column>
            <el-table-column label="工序进度" min-width="160">
              <template #default="{ row }">
                <el-progress :percentage="pct(row)" :stroke-width="10" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="VAT_STATUS[row.status]?.type" size="small">{{ row.status_display }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never" header="最新质量异常">
          <el-timeline style="padding-left: 4px">
            <el-timeline-item v-for="i in data.recent_issues" :key="i.id"
              :type="i.status === 'closed' ? 'success' : i.severity === 'critical' ? 'danger' : 'warning'"
              :timestamp="i.created_at">
              <b>{{ i.vat_no }}</b> {{ i.issue_type_display }}（{{ i.severity_display }}）
              <el-tag size="small" :type="ISSUE_STATUS[i.status]?.type" style="margin-left: 6px">{{ i.status_display }}</el-tag>
              <div style="color: #909399; font-size: 12px; margin-top: 4px">{{ i.description }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '../api'
import { VAT_STATUS, ISSUE_STATUS } from '../status'

const loading = ref(true)
const data = ref({ recent_issues: [], producing_vats: [] })
const cards = ref([])
const orderChart = ref(null)
const vatChart = ref(null)
const issueChart = ref(null)

const pct = (row) => (row.total_steps ? Math.round((row.done_steps / row.total_steps) * 100) : 0)

const ORDER_LABEL = { pending: '待生产', producing: '生产中', completed: '已完成', shipped: '已出货' }
const VAT_LABEL = { unscheduled: '待排缸', scheduled: '已排缸', producing: '生产中', inspecting: '待检验', completed: '已完成' }
const ISSUE_LABEL = { color_diff: '色差', color_flower: '色花', stain: '沾污', fastness: '色牢度', defect: '疵点', strength: '强力', other: '其他' }

function pie(el, title, obj, labels, colors) {
  const chart = echarts.init(el)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    color: colors,
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      label: { formatter: '{b}: {c}' },
      data: Object.entries(obj || {}).map(([k, v]) => ({ name: labels[k] || k, value: v })),
    }],
  })
}

onMounted(async () => {
  const res = await api.dashboard()
  data.value = res.data
  const d = res.data
  cards.value = [
    { label: '订单总数', value: d.order_total, color: '#409eff' },
    { label: '生产中缸号', value: d.vat_producing, color: '#e6a23c' },
    { label: '待排缸', value: d.vat_unscheduled, color: '#909399' },
    { label: '待处理异常', value: d.issue_open, color: '#f56c6c' },
    { label: '返修中', value: d.rework_active, color: '#b37feb' },
    { label: '累计产出(kg)', value: d.total_output_kg, color: '#67c23a' },
  ]
  loading.value = false
  await nextTick()
  pie(orderChart.value, '订单', d.orders_by_status, ORDER_LABEL, ['#909399', '#e6a23c', '#67c23a', '#409eff'])
  pie(vatChart.value, '缸号', d.vats_by_status, VAT_LABEL, ['#909399', '#409eff', '#e6a23c', '#f56c6c', '#67c23a'])
  pie(issueChart.value, '异常', d.issues_by_type, ISSUE_LABEL, ['#f56c6c', '#e6a23c', '#b37feb', '#409eff', '#67c23a', '#909399', '#13c2c2'])
})
</script>
