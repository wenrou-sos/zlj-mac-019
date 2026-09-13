<template>
  <div>
    <el-card shadow="never">
      <div style="display: flex; gap: 12px; margin-bottom: 16px">
        <el-input v-model="keyword" placeholder="搜索订单号 / 客户" clearable style="width: 240px"
          @keyup.enter="load" @clear="load">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px" @change="load">
          <el-option v-for="(v, k) in ORDER_STATUS" :key="k" :label="v.text" :value="k" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" icon="Plus" @click="openForm()">新建订单</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" @row-click="(r) => $router.push(`/orders/${r.id}`)" style="cursor: pointer">
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="customer" label="客户" width="110" />
        <el-table-column prop="fabric_type" label="布种" min-width="140" />
        <el-table-column prop="color" label="颜色" width="80">
          <template #default="{ row }">{{ row.color }}<span v-if="row.color_no" style="color:#909399"> ({{ row.color_no }})</span></template>
        </el-table-column>
        <el-table-column prop="quantity_kg" label="数量(kg)" width="100" align="right" />
        <el-table-column label="已分缸" width="90" align="center">
          <template #default="{ row }">{{ row.vat_count }} 缸</template>
        </el-table-column>
        <el-table-column prop="delivery_date" label="交期" width="110" />
        <el-table-column label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="PRIORITY[row.priority]?.type" size="small">{{ row.priority_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="ORDER_STATUS[row.status]?.type" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="openForm(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click.stop="$router.push(`/orders/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑订单' : '新建订单'" width="560px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="订单号" required><el-input v-model="form.order_no" :disabled="!!form.id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="客户" required><el-input v-model="form.customer" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="布种" required><el-input v-model="form.fabric_type" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="成分"><el-input v-model="form.composition" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="颜色" required><el-input v-model="form.color" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="色号"><el-input v-model="form.color_no" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="数量(kg)" required><el-input-number v-model="form.quantity_kg" :min="1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="交期" required><el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width: 100%">
                <el-option v-for="(v, k) in PRIORITY" :key="k" :label="v.text" :value="k" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="(v, k) in ORDER_STATUS" :key="k" :label="v.text" :value="k" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import { ORDER_STATUS, PRIORITY } from '../status'

const rows = ref([])
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const dialogVisible = ref(false)
const saving = ref(false)
const blank = { order_no: '', customer: '', fabric_type: '', composition: '', color: '', color_no: '', quantity_kg: 1000, delivery_date: '', priority: 'normal', status: 'pending', remark: '' }
const form = ref({ ...blank })

async function load() {
  loading.value = true
  try {
    const res = await api.orders({ keyword: keyword.value || undefined, status: statusFilter.value || undefined })
    rows.value = res.data
  } finally {
    loading.value = false
  }
}

function openForm(row) {
  form.value = row ? { ...row } : { ...blank }
  dialogVisible.value = true
}

async function save() {
  saving.value = true
  try {
    if (form.value.id) await api.updateOrder(form.value.id, form.value)
    else await api.createOrder(form.value)
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data ? JSON.stringify(e.response.data) : '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
