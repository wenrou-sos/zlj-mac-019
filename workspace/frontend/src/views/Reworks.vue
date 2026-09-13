<template>
  <div>
    <el-card shadow="never">
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="id" label="单号" width="80">
          <template #default="{ row }">RW-{{ String(row.id).padStart(3, '0') }}</template>
        </el-table-column>
        <el-table-column prop="issue_no" label="关联异常" width="150" />
        <el-table-column prop="vat_no" label="缸号" width="130" />
        <el-table-column prop="issue_type_display" label="异常类型" width="110" />
        <el-table-column prop="rework_type_display" label="返修方式" width="100" />
        <el-table-column prop="plan" label="处理方案" min-width="240" show-overflow-tooltip />
        <el-table-column prop="operator" label="负责人" width="90" />
        <el-table-column prop="created_at" label="创建时间" width="130" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="REWORK_STATUS[row.status]?.type" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.result === 'pass'" type="success" size="small">合格</el-tag>
            <el-tag v-else-if="row.result === 'fail'" type="danger" size="small">不合格</el-tag>
            <span v-else style="color: #909399">待定</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" link type="warning" size="small" @click="start(row)">开始处理</el-button>
            <template v-if="row.status !== 'done'">
              <el-button link type="success" size="small" @click="finish(row, 'pass')">合格结案</el-button>
              <el-button link type="danger" size="small" @click="finish(row, 'fail')">不合格</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { REWORK_STATUS } from '../status'

const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await api.reworks()
    rows.value = res.data
  } finally {
    loading.value = false
  }
}

async function start(row) {
  await api.updateRework(row.id, { status: 'processing' })
  ElMessage.success('已开始处理')
  load()
}

async function finish(row, result) {
  const text = result === 'pass' ? '确认返修合格？关联异常将自动关闭。' : '确认返修不合格？异常将退回「待处理」，可再次发起返修。'
  await ElMessageBox.confirm(text, '返修结案', { type: result === 'pass' ? 'success' : 'warning' })
  await api.finishRework(row.id, result)
  ElMessage.success('已结案')
  load()
}

onMounted(load)
</script>
