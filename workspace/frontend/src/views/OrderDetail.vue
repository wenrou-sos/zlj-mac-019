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

      <el-alert v-if="order.risk && order.risk.level !== 'ok'" style="margin-top: 16px" show-icon :closable="false"
        :type="order.risk.level === 'overdue' ? 'error' : 'warning'"
        :title="order.risk.level === 'overdue' ? '订单已拖期' : '订单有拖期风险'">
        <template #default>
          <div v-for="(r, i) in order.risk.reasons" :key="i" style="font-size: 13px">{{ r }}</div>
        </template>
      </el-alert>

      <el-card shadow="never" style="margin-top: 16px">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <b>缸号列表</b>
            <el-button type="primary" size="small" icon="Plus" @click="openVatDialog">新增缸号</el-button>
          </div>
        </template>
        <el-collapse v-model="expanded">
          <el-collapse-item v-for="v in order.vats" :key="v.id" :name="v.id">
            <template #title>
              <div style="display: flex; align-items: center; gap: 14px; width: 100%">
                <b>{{ v.vat_no }}</b>
                <el-tag size="small" :type="VAT_STATUS[v.status]?.type">{{ v.status_display }}</el-tag>
                <span style="color: #606266">
                  {{ v.weight_kg }} kg
                  <el-button link type="primary" size="small" icon="Edit" @click.stop="openWeightEdit(v)" />
                </span>
                <span style="color: #909399; font-size: 13px">机台：{{ v.machine_name || '未排缸' }}</span>
                <el-tooltip v-if="v.schedule_warnings?.length" placement="top">
                  <template #content>
                    <div v-for="(w, i) in v.schedule_warnings" :key="i">{{ w }}</div>
                  </template>
                  <el-icon color="#f56c6c"><WarningFilled /></el-icon>
                </el-tooltip>
                <el-tooltip v-if="v.delay_info?.delayed" :content="v.delay_info.reason" placement="top">
                  <el-tag size="small" type="danger" effect="plain">落后</el-tag>
                </el-tooltip>
                <el-progress :percentage="pct(v)" :stroke-width="8" style="width: 180px" />
              </div>
            </template>
            <VatPanel :vat-id="v.id" @changed="load" />
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </template>

    <el-dialog v-model="vatDialog" title="新增缸号" width="480px">
      <el-form label-width="90px">
        <el-form-item label="缸号" required><el-input v-model="newVat.vat_no" placeholder="如 VAT202609-019" /></el-form-item>
        <el-form-item label="重量(kg)" required><el-input-number v-model="newVat.weight_kg" :min="1" style="width: 100%" /></el-form-item>
        <el-form-item label="初始工艺">
          <el-radio-group v-model="newVat.mode">
            <el-radio-button value="default">默认参数</el-radio-button>
            <el-radio-button value="template">套用模板</el-radio-button>
            <el-radio-button value="copy">复制缸号</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="newVat.mode === 'template'" label="工艺模板">
          <el-select v-model="newVat.template_id" filterable style="width: 100%" placeholder="选择模板">
            <el-option v-for="t in sortedTemplates" :key="t.id" :value="t.id"
              :label="`${t.name}（${t.dye_temp}℃ ${t.dye_time}min）`">
              <span>{{ t.name }}</span>
              <span v-if="isTemplateMatch(t)" style="float: right; color: #67c23a; font-size: 12px">匹配本单</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-if="newVat.mode === 'copy'" label="来源缸号">
          <el-select v-model="newVat.copy_from" filterable style="width: 100%" placeholder="选择已有缸号">
            <el-option v-for="v in allVats" :key="v.id" :value="v.id"
              :label="`${v.vat_no}（${v.order_no} ${v.color}）`" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="vatDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createVat">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="weightDialog" :title="`修改重量 - ${weightEdit.vat_no}`" width="360px">
      <el-input-number v-model="weightEdit.weight_kg" :min="1" style="width: 100%" />
      <template #footer>
        <el-button @click="weightDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWeight">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import { ORDER_STATUS, PRIORITY, VAT_STATUS } from '../status'
import VatPanel from '../components/VatPanel.vue'

const route = useRoute()
const order = ref(null)
const loading = ref(true)
const saving = ref(false)
const expanded = ref([])
const vatDialog = ref(false)
const newVat = ref({ vat_no: '', weight_kg: 500, mode: 'default', template_id: null, copy_from: null })
const templates = ref([])
const allVats = ref([])
const weightDialog = ref(false)
const weightEdit = ref({ id: null, vat_no: '', weight_kg: 0 })

const vatWeightSum = computed(() => (order.value ? order.value.vats.reduce((s, v) => s + Number(v.weight_kg), 0).toFixed(1) : 0))
const pct = (v) => (v.total_steps ? Math.round((v.done_steps / v.total_steps) * 100) : 0)

const isTemplateMatch = (t) =>
  order.value && t.fabric_type === order.value.fabric_type && (!order.value.color_no || t.color_no === order.value.color_no)

const sortedTemplates = computed(() =>
  [...templates.value].sort((a, b) => (isTemplateMatch(b) ? 1 : 0) - (isTemplateMatch(a) ? 1 : 0))
)

async function load() {
  loading.value = true
  try {
    const res = await api.order(route.params.id)
    order.value = res.data
  } finally {
    loading.value = false
  }
}

async function openVatDialog() {
  newVat.value = { vat_no: '', weight_kg: 500, mode: 'default', template_id: null, copy_from: null }
  const [t, v] = await Promise.all([api.templates(), api.vats()])
  templates.value = t.data
  allVats.value = v.data
  // 默认选中匹配本单布种色号的模板
  const match = t.data.find((x) => isTemplateMatch(x))
  if (match) {
    newVat.value.mode = 'template'
    newVat.value.template_id = match.id
  }
  vatDialog.value = true
}

async function createVat() {
  saving.value = true
  try {
    const payload = { vat_no: newVat.value.vat_no, weight_kg: newVat.value.weight_kg, order: order.value.id }
    if (newVat.value.mode === 'template' && newVat.value.template_id) payload.template_id = newVat.value.template_id
    if (newVat.value.mode === 'copy' && newVat.value.copy_from) payload.copy_from = newVat.value.copy_from
    await api.createVat(payload)
    ElMessage.success('缸号已创建')
    vatDialog.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data ? JSON.stringify(e.response.data) : '创建失败')
  } finally {
    saving.value = false
  }
}

function openWeightEdit(v) {
  weightEdit.value = { id: v.id, vat_no: v.vat_no, weight_kg: Number(v.weight_kg) }
  weightDialog.value = true
}

async function saveWeight() {
  const res = await api.updateVat(weightEdit.value.id, { weight_kg: weightEdit.value.weight_kg })
  weightDialog.value = false
  ElMessage.success('重量已更新')
  // 已排缸号改重量后重新校验，有警告立即提示
  const warnings = res.data.schedule_warnings || []
  if (warnings.length) {
    ElMessageBox.alert(warnings.join('<br>'), '该缸已排产，请注意', {
      type: 'warning',
      dangerouslyUseHTMLString: true,
      confirmButtonText: '知道了',
    })
  }
  load()
}

onMounted(load)
</script>
