<template>
  <div>
    <el-card shadow="never">
      <div style="display: flex; gap: 12px; margin-bottom: 16px">
        <el-radio-group v-model="filter" @change="load">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="producing">生产中</el-radio-button>
          <el-radio-button value="scheduled">已排缸</el-radio-button>
          <el-radio-button value="inspecting">待检验</el-radio-button>
          <el-radio-button value="completed">已完成</el-radio-button>
        </el-radio-group>
      </div>
      <el-table :data="rows" v-loading="loading" row-key="id" :expand-row-keys="expanded">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div style="padding: 8px 24px"><VatPanel :vat-id="row.id" @changed="load" /></div>
          </template>
        </el-table-column>
        <el-table-column prop="vat_no" label="缸号" width="140" />
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="customer" label="客户" width="110" />
        <el-table-column prop="color" label="颜色" width="80" />
        <el-table-column prop="machine_name" label="机台" width="120">
          <template #default="{ row }">{{ row.machine_name || '—' }}</template>
        </el-table-column>
        <el-table-column label="工序进度" min-width="200">
          <template #default="{ row }">
            <el-progress :percentage="pct(row)" :stroke-width="12"
              :status="row.status === 'completed' ? 'success' : ''" />
          </template>
        </el-table-column>
        <el-table-column label="当前工序" width="130">
          <template #default="{ row }">{{ row.current_step }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="VAT_STATUS[row.status]?.type" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { VAT_STATUS } from '../status'
import VatPanel from '../components/VatPanel.vue'

const rows = ref([])
const loading = ref(false)
const filter = ref('')
const expanded = ref([])

const pct = (row) => (row.total_steps ? Math.round((row.done_steps / row.total_steps) * 100) : 0)

async function load() {
  loading.value = true
  try {
    const res = await api.vats({ status: filter.value || undefined })
    rows.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
