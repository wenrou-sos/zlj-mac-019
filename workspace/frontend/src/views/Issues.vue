<template>
  <div>
    <el-card shadow="never">
      <div style="display: flex; justify-content: space-between; margin-bottom: 16px">
        <el-radio-group v-model="statusFilter" @change="load">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="open">待处理</el-radio-button>
          <el-radio-button value="processing">处理中</el-radio-button>
          <el-radio-button value="closed">已关闭</el-radio-button>
        </el-radio-group>
        <el-button type="danger" icon="Plus" @click="openForm">上报异常</el-button>
      </div>

      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="issue_no" label="异常单号" width="150" />
        <el-table-column prop="vat_no" label="缸号" width="130" />
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">{{ row.issue_type_display }}</template>
        </el-table-column>
        <el-table-column label="严重程度" width="90">
          <template #default="{ row }">
            <el-tag :type="SEVERITY[row.severity]?.type" size="small">{{ row.severity_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="异常描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="reporter" label="上报人" width="90" />
        <el-table-column prop="created_at" label="上报时间" width="130" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="ISSUE_STATUS[row.status]?.type" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="返修" width="70" align="center">
          <template #default="{ row }">
            <el-badge v-if="row.rework_count" :value="row.rework_count" type="warning">
              <el-icon><RefreshLeft /></el-icon>
            </el-badge>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'open'" link type="warning" size="small" @click="transition(row, 'processing')">开始处理</el-button>
            <el-button v-if="row.status !== 'closed'" link type="success" size="small" @click="transition(row, 'closed')">关闭</el-button>
            <el-button v-if="row.status !== 'closed'" link type="primary" size="small" @click="openRework(row)">发起返修</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="上报质量异常" width="520px">
      <el-form label-width="90px">
        <el-form-item label="缸号" required>
          <el-select v-model="form.vat" filterable style="width: 100%" placeholder="选择缸号">
            <el-option v-for="v in vats" :key="v.id" :label="`${v.vat_no}（${v.order_no} ${v.color}）`" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="异常类型" required>
          <el-select v-model="form.issue_type" style="width: 100%">
            <el-option v-for="t in ISSUE_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-radio-group v-model="form.severity">
            <el-radio-button value="minor">轻微</el-radio-button>
            <el-radio-button value="major">一般</el-radio-button>
            <el-radio-button value="critical">严重</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="异常描述" required>
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="如：对样偏红光，△E=1.8" />
        </el-form-item>
        <el-form-item label="上报人" required>
          <el-input v-model="form.reporter" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="save">提交上报</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reworkDialog" :title="`发起返修 - ${currentIssue?.issue_no || ''}`" width="520px">
      <el-form label-width="90px">
        <el-form-item label="返修方式">
          <el-select v-model="reworkForm.rework_type" style="width: 100%">
            <el-option v-for="t in REWORK_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理方案" required>
          <el-input v-model="reworkForm.plan" type="textarea" :rows="3" placeholder="如：剥色后按1.0℃/min升温重染" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="reworkForm.operator" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reworkDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRework">创建返修单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import { ISSUE_STATUS, SEVERITY, ISSUE_TYPES, REWORK_TYPES } from '../status'

const rows = ref([])
const vats = ref([])
const loading = ref(false)
const statusFilter = ref('')
const dialogVisible = ref(false)
const reworkDialog = ref(false)
const saving = ref(false)
const currentIssue = ref(null)
const form = ref({ vat: null, issue_type: 'color_diff', severity: 'major', description: '', reporter: '' })
const reworkForm = ref({ rework_type: 'redye', plan: '', operator: '' })

async function load() {
  loading.value = true
  try {
    const res = await api.issues({ status: statusFilter.value || undefined })
    rows.value = res.data
  } finally {
    loading.value = false
  }
}

async function openForm() {
  const res = await api.vats()
  vats.value = res.data
  form.value = { vat: null, issue_type: 'color_diff', severity: 'major', description: '', reporter: '' }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.vat || !form.value.description || !form.value.reporter) return ElMessage.warning('请填写完整')
  saving.value = true
  try {
    await api.createIssue(form.value)
    ElMessage.success('异常已上报')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function transition(row, status) {
  await api.transitionIssue(row.id, status)
  ElMessage.success('状态已更新')
  load()
}

function openRework(issue) {
  currentIssue.value = issue
  reworkForm.value = { rework_type: 'redye', plan: '', operator: '' }
  reworkDialog.value = true
}

async function saveRework() {
  if (!reworkForm.value.plan) return ElMessage.warning('请填写处理方案')
  saving.value = true
  try {
    await api.createRework({ ...reworkForm.value, issue: currentIssue.value.id })
    ElMessage.success('返修单已创建')
    reworkDialog.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
