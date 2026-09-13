<template>
  <div v-loading="loading">
    <el-row :gutter="20" v-if="vat">
      <el-col :span="11">
        <div class="section-title">
          <b>工艺参数</b>
          <el-button size="small" type="primary" link icon="Edit" @click="editParams">编辑</el-button>
        </div>
        <template v-if="vat.params">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="浴比">{{ vat.params.bath_ratio }}</el-descriptions-item>
            <el-descriptions-item label="染色温度">{{ vat.params.dye_temp }} ℃</el-descriptions-item>
            <el-descriptions-item label="保温时间">{{ vat.params.dye_time }} min</el-descriptions-item>
            <el-descriptions-item label="pH值">{{ vat.params.ph_value }}</el-descriptions-item>
            <el-descriptions-item label="升温速率">{{ vat.params.heating_rate }} ℃/min</el-descriptions-item>
            <el-descriptions-item label="计划时间">{{ vat.planned_start || '—' }} ~ {{ vat.planned_end || '—' }}</el-descriptions-item>
          </el-descriptions>
          <el-table :data="vat.params.dyes" size="small" style="margin-top: 8px">
            <el-table-column label="染料" prop="name" />
            <el-table-column label="用量(%)" prop="pct" width="100" align="right" />
          </el-table>
          <el-table :data="vat.params.auxiliaries" size="small" style="margin-top: 8px">
            <el-table-column label="助剂" prop="name" />
            <el-table-column label="用量(g/L)" prop="gpl" width="110" align="right" />
          </el-table>
          <div v-if="vat.params.note" style="color: #909399; font-size: 12px; margin-top: 8px">备注：{{ vat.params.note }}</div>
        </template>
        <el-empty v-else description="暂无工艺参数" :image-size="60" />
      </el-col>

      <el-col :span="13">
        <div class="section-title"><b>工序进度</b></div>
        <el-steps :active="activeStep" direction="vertical" style="height: auto">
          <el-step v-for="s in vat.steps" :key="s.id" :title="s.step_display"
            :status="stepStatus(s)">
            <template #description>
              <div style="font-size: 12px; color: #909399">
                <span v-if="s.operator">操作工：{{ s.operator }}　</span>
                <span v-if="s.start_time">{{ s.start_time }}<template v-if="s.end_time"> ~ {{ s.end_time }}</template></span>
              </div>
              <div style="margin-top: 4px" v-if="s.status !== 'done'">
                <el-button size="small" type="primary" plain @click="advance(s)">
                  {{ s.status === 'not_started' ? '开始' : s.status === 'abnormal' ? '恢复' : '完成' }}
                </el-button>
                <el-button v-if="s.status === 'in_progress'" size="small" type="danger" plain @click="abnormal(s)">标记异常</el-button>
              </div>
            </template>
          </el-step>
        </el-steps>
      </el-col>
    </el-row>

    <el-dialog v-model="paramDialog" title="编辑工艺参数" width="640px" append-to-body>
      <el-form v-if="paramForm" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="浴比"><el-input v-model="paramForm.bath_ratio" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="染色温度(℃)"><el-input-number v-model="paramForm.dye_temp" :step="1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="保温时间(min)"><el-input-number v-model="paramForm.dye_time" :min="0" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="pH值"><el-input-number v-model="paramForm.ph_value" :step="0.1" :min="0" :max="14" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="升温速率"><el-input-number v-model="paramForm.heating_rate" :step="0.1" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="染料配方">
          <div v-for="(d, i) in paramForm.dyes" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px; width: 100%">
            <el-input v-model="d.name" placeholder="染料名称" style="flex: 1" />
            <el-input-number v-model="d.pct" :step="0.1" :min="0" placeholder="%" style="width: 130px" />
            <el-button link type="danger" icon="Delete" @click="paramForm.dyes.splice(i, 1)" />
          </div>
          <el-button size="small" icon="Plus" @click="paramForm.dyes.push({ name: '', pct: 0 })">加染料</el-button>
        </el-form-item>
        <el-form-item label="助剂">
          <div v-for="(a, i) in paramForm.auxiliaries" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px; width: 100%">
            <el-input v-model="a.name" placeholder="助剂名称" style="flex: 1" />
            <el-input-number v-model="a.gpl" :step="0.1" :min="0" placeholder="g/L" style="width: 130px" />
            <el-button link type="danger" icon="Delete" @click="paramForm.auxiliaries.splice(i, 1)" />
          </div>
          <el-button size="small" icon="Plus" @click="paramForm.auxiliaries.push({ name: '', gpl: 0 })">加助剂</el-button>
        </el-form-item>
        <el-form-item label="工艺备注"><el-input v-model="paramForm.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paramDialog = false">取消</el-button>
        <el-button type="primary" @click="saveParams">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const props = defineProps({ vatId: { type: Number, required: true } })
const emit = defineEmits(['changed'])

const vat = ref(null)
const loading = ref(false)
const paramDialog = ref(false)
const paramForm = ref(null)

const activeStep = computed(() => (vat.value ? vat.value.steps.filter((s) => s.status === 'done').length : 0))

function stepStatus(s) {
  if (s.status === 'done') return 'success'
  if (s.status === 'abnormal') return 'error'
  if (s.status === 'in_progress') return 'process'
  return 'wait'
}

async function load() {
  loading.value = true
  try {
    const res = await api.vat(props.vatId)
    vat.value = res.data
  } finally {
    loading.value = false
  }
}

function editParams() {
  if (!vat.value.params) return ElMessage.warning('该缸号暂无工艺参数记录')
  paramForm.value = JSON.parse(JSON.stringify(vat.value.params))
  paramDialog.value = true
}

async function saveParams() {
  try {
    await api.updateParams(paramForm.value.id, paramForm.value)
    ElMessage.success('工艺参数已保存')
    paramDialog.value = false
    load()
  } catch {
    ElMessage.error('保存失败')
  }
}

async function advance(step) {
  const operator = step.operator || '张挡车'
  await api.advanceStep(step.id, operator)
  ElMessage.success(`「${step.step_display}」已推进`)
  load()
  emit('changed')
}

async function abnormal(step) {
  await ElMessageBox.confirm(`确认将「${step.step_display}」标记为异常？请到质量异常页上报详情。`, '提示', { type: 'warning' })
  await api.abnormalStep(step.id)
  ElMessage.warning('已标记异常')
  load()
  emit('changed')
}

watch(() => props.vatId, load, { immediate: true })
</script>

<style scoped>
.section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
</style>
