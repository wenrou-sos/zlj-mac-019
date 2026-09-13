<template>
  <div v-loading="loading">
    <template v-if="order">
      <el-card shadow="never">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span><b>{{ order.order_no }}</b> · {{ order.customer }}</span>
            <div>
              <el-tag :type="PRIORITY[order.priority]?.type" style="margin-right: 8px">{{ order.priority_display }}</el-tag>
              <el-tag :type="ORDER_STATUS[order.status]?.type">{{ order.status_display }}</el-tag>
            </div>
          </div>
        </template>
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="布种">{{ order.fabric_type }}</el-descriptions-item>
          <el-descriptions-item label="成分">{{ order.composition || '—' }}</el-descriptions-item>
          <el-descriptions-item label="颜色">{{ order.color }}（{{ order.color_no || '—' }}）</el-descriptions-item>
          <el-descriptions-item label="数量">{{ order.quantity_kg }} kg</el-descriptions-item>
          <el-descriptions-item label="交期">{{ order.delivery_date }}</el-descriptions-item>
          <el-descriptions-item label="已分缸">{{ order.vats.length }} 缸 / {{ vatWeightSum }} kg</el-descriptions-item>
          <el-descriptions-item label="已完成">{{ order.produced_kg }} kg</el-descriptions-item>
          <el-descriptions-item label="备注">{{ order.remark || '—' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <b>缸号列表</b>
            <el-button type="primary" size="small" icon="Plus" @click="vatDialog = true">新增缸号</el-button>
          </div>
        </template>
        <el-collapse v-model="expanded">
          <el-collapse-item v-for="v in order.vats" :key="v.id" :name="v.id">
            <template #title>
              <div style="display: flex; align-items: center; gap: 14px; width: 100%">
                <b>{{ v.vat_no }}</b>
                <el-tag size="small" :type="VAT_STATUS[v.status]?.type">{{ v.status_display }}</el-tag>
                <span style="color: #606266">{{ v.weight_kg }} kg</span>
                <span style="color: #909399; font-size: 13px">机台：{{ v.machine_name || '未排缸' }}</span>
                <el-progress :percentage="pct(v)" :stroke-width="8" style="width: 180px" />
              </div>
            </template>
            <VatPanel :vat-id="v.id" @changed="load" />
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </template>

    <el-dialog v-model="vatDialog" title="新增缸号" width="420px">
      <el-form label-width="90px">
        <el-form-item label="缸号" required><el-input v-model="newVat.vat_no" placeholder="如 VAT202609-019" /></el-form-item>
        <el-form-item label="重量(kg)" required><el-input-number v-model="newVat.weight_kg" :min="1" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="vatDialog = false">取消</el-button>
        <el-button type="primary" @click="createVat">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import { ORDER_STATUS, PRIORITY, VAT_STATUS } from '../status'
import VatPanel from '../components/VatPanel.vue'

const route = useRoute()
const order = ref(null)
const loading = ref(true)
const expanded = ref([])
const vatDialog = ref(false)
const newVat = ref({ vat_no: '', weight_kg: 500 })

const vatWeightSum = computed(() => (order.value ? order.value.vats.reduce((s, v) => s + Number(v.weight_kg), 0).toFixed(1) : 0))
const pct = (v) => (v.total_steps ? Math.round((v.done_steps / v.total_steps) * 100) : 0)

async function load() {
  loading.value = true
  try {
    const res = await api.order(route.params.id)
    order.value = res.data
  } finally {
    loading.value = false
  }
}

async function createVat() {
  try {
    await api.createVat({ ...newVat.value, order: order.value.id })
    ElMessage.success('缸号已创建')
    vatDialog.value = false
    newVat.value = { vat_no: '', weight_kg: 500 }
    load()
  } catch (e) {
    ElMessage.error(e.response?.data ? JSON.stringify(e.response.data) : '创建失败')
  }
}

onMounted(load)
</script>
