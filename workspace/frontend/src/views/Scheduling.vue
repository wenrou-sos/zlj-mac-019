<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="never">
          <template #header><b>待排缸（{{ unscheduled.length }}）</b></template>
          <div v-for="v in sortedUnscheduled" :key="v.id" class="vat-item" :class="{ urgent: v.order_priority !== 'normal' }">
            <div>
              <b>{{ v.vat_no }}</b>
              <el-tag size="small" style="margin-left: 6px">{{ v.color }}</el-tag>
              <el-tag v-if="v.order_priority !== 'normal'" size="small" effect="dark"
                :type="v.order_priority === 'critical' ? 'danger' : 'warning'" style="margin-left: 4px">
                {{ v.order_priority_display }}
              </el-tag>
              <div style="color: #909399; font-size: 12px; margin-top: 4px">
                {{ v.order_no }} · {{ v.fabric_type }} · {{ v.weight_kg }} kg
              </div>
              <div style="font-size: 12px; margin-top: 2px"
                :style="{ color: deliveryUrgent(v.order_delivery) ? '#f56c6c' : '#909399' }">
                交期 {{ v.order_delivery }}<span v-if="deliveryUrgent(v.order_delivery)">（临近/已过）</span>
              </div>
            </div>
            <el-button size="small" type="primary" @click="openSchedule(v)">排缸</el-button>
          </div>
          <el-empty v-if="!unscheduled.length" description="没有待排缸号" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="18">
        <el-row :gutter="12">
          <el-col :span="8" v-for="col in board" :key="col.machine.id">
            <el-card shadow="never" class="machine-card">
              <template #header>
                <div>
                  <b>{{ col.machine.name }}</b>
                  <div style="color: #909399; font-size: 12px">{{ col.machine.machine_type_display }} · {{ col.machine.capacity_kg }}kg</div>
                </div>
              </template>
              <div v-for="v in col.vats" :key="v.id" class="scheduled-item" :class="[v.status, { 'has-warning': v.schedule_warnings?.length }]">
                <div style="display: flex; justify-content: space-between; align-items: center">
                  <span>
                    <b>{{ v.vat_no }}</b>
                    <el-tooltip v-if="v.schedule_warnings?.length" placement="top">
                      <template #content>
                        <div v-for="(w, i) in v.schedule_warnings" :key="i">{{ w }}</div>
                      </template>
                      <el-icon color="#f56c6c" style="vertical-align: -2px; margin-left: 4px"><WarningFilled /></el-icon>
                    </el-tooltip>
                    <el-tooltip v-if="v.delay_info?.delayed" :content="v.delay_info.reason" placement="top">
                      <el-tag size="small" type="danger" effect="plain" style="margin-left: 4px">落后</el-tag>
                    </el-tooltip>
                  </span>
                  <el-tag size="small" :type="VAT_STATUS[v.status]?.type">{{ v.status_display }}</el-tag>
                </div>
                <div style="color: #606266; font-size: 12px; margin-top: 4px">
                  {{ v.order_no }} · {{ v.color }} · {{ v.weight_kg }}kg
                </div>
                <div style="color: #909399; font-size: 12px; margin-top: 2px">
                  {{ v.planned_start || '缺计划时间' }} ~ {{ v.planned_end || '' }}
                </div>
                <el-button v-if="v.status === 'scheduled'" link type="danger" size="small" @click="unschedule(v)">取消排缸</el-button>
              </div>
              <el-empty v-if="!col.vats.length" description="空闲" :image-size="50" />
            </el-card>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="`排缸 - ${current?.vat_no || ''}（${current?.weight_kg ?? ''}kg）`" width="560px">
      <el-alert v-if="current && current.order_priority !== 'normal'" class="urgent-alert"
        :type="current.order_priority === 'critical' ? 'error' : 'warning'" show-icon :closable="false"
        :title="`该缸属于${current.order_priority_display}订单，交期 ${current.order_delivery}，请优先安排`"
        style="margin-bottom: 12px" />
      <el-form label-width="90px">
        <el-form-item label="机台" required>
          <el-select v-model="form.machine" style="width: 100%">
            <el-option v-for="m in machines" :key="m.id" :value="m.id"
              :label="`${m.name}（${m.machine_type_display} ${m.capacity_kg}kg）`">
              <span>{{ m.name }}（{{ m.machine_type_display }} {{ m.capacity_kg }}kg）</span>
              <span v-if="current && m.capacity_kg < current.weight_kg" style="float: right; color: #f56c6c; font-size: 12px">超容，需确认</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="计划时间" required>
          <el-date-picker v-model="form.range" type="datetimerange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
      </el-form>

      <div v-loading="checking">
        <el-alert v-for="(w, i) in check.warnings" :key="'w' + i" :title="w" type="warning" show-icon :closable="false"
          description="属于超容/机型不适配，提交时需人工确认后方可排入" style="margin-bottom: 8px" />
        <el-alert v-if="check.conflict" type="error" show-icon :closable="false" style="margin-bottom: 8px">
          <template #title>
            时段冲突：{{ check.conflict }}
            <template v-if="check.next_available">
              ，下一空档 {{ fmt(check.next_available[0]) }} ~ {{ fmt(check.next_available[1]) }}
              <el-button link type="primary" size="small" @click="useNextSlot">使用此时段</el-button>
            </template>
          </template>
        </el-alert>
        <el-alert v-if="check.merge_suggestions?.length" type="success" show-icon :closable="false"
          title="拼缸建议：以下同布种同色号待排缸可同缸合染" style="margin-bottom: 8px">
          <template #default>
            <div v-for="s in check.merge_suggestions" :key="s.vat_no" style="font-size: 12px">
              {{ s.vat_no }}（{{ s.order_no }} · {{ s.weight_kg }}kg）
            </div>
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!!check.conflict" @click="save(false)">确认排缸</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import api from '../api'
import { VAT_STATUS } from '../status'

const board = ref([])
const unscheduled = ref([])
const machines = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const checking = ref(false)
const current = ref(null)
const form = ref({ machine: null, range: null })
const check = ref({ warnings: [], conflict: null, next_available: null, merge_suggestions: [] })

const fmt = (t) => dayjs(t).format('MM-DD HH:mm')

const PRIORITY_ORDER = { critical: 0, urgent: 1, normal: 2 }

// 待排缸：加急/特急优先，同级按交期升序
const sortedUnscheduled = computed(() =>
  [...unscheduled.value].sort((a, b) => {
    const p = (PRIORITY_ORDER[a.order_priority] ?? 2) - (PRIORITY_ORDER[b.order_priority] ?? 2)
    return p !== 0 ? p : String(a.order_delivery).localeCompare(String(b.order_delivery))
  })
)

// 交期临近（<=2天）或已过
const deliveryUrgent = (d) => d && dayjs(d).diff(dayjs().startOf('day'), 'day') <= 2

async function load() {
  const [b, u, m] = await Promise.all([
    api.machineBoard(),
    api.vats({ status: 'unscheduled' }),
    api.machines(),
  ])
  board.value = b.data
  unscheduled.value = u.data
  machines.value = m.data.filter((x) => x.is_active)
}

function openSchedule(vat) {
  current.value = vat
  check.value = { warnings: [], conflict: null, next_available: null, merge_suggestions: [] }
  const start = dayjs().add(1, 'day').hour(8).minute(0).second(0)
  form.value = {
    machine: null,
    range: [start.format('YYYY-MM-DDTHH:mm:ss'), start.add(10, 'hour').format('YYYY-MM-DDTHH:mm:ss')],
  }
  dialogVisible.value = true
}

// 机台或时段变化时实时预检
watch(
  () => [form.value.machine, form.value.range],
  async () => {
    check.value = { warnings: [], conflict: null, next_available: null, merge_suggestions: [] }
    if (!dialogVisible.value || !form.value.machine || !form.value.range || form.value.range.length !== 2) return
    checking.value = true
    try {
      const res = await api.scheduleCheck(current.value.id, {
        machine: form.value.machine,
        planned_start: form.value.range[0],
        planned_end: form.value.range[1],
      })
      check.value = res.data
    } catch {
      /* 参数不完整时后端会 400，静默忽略，提交时再提示 */
    } finally {
      checking.value = false
    }
  },
  { deep: true }
)

function useNextSlot() {
  const [s, e] = check.value.next_available
  form.value.range = [dayjs(s).format('YYYY-MM-DDTHH:mm:ss'), dayjs(e).format('YYYY-MM-DDTHH:mm:ss')]
}

async function doSchedule(payload) {
  await api.scheduleVat(current.value.id, payload)
  ElMessage.success('排缸成功')
  dialogVisible.value = false
  load()
}

async function save(confirmed) {
  if (!form.value.machine || !form.value.range || form.value.range.length !== 2) {
    return ElMessage.warning('请选择机台和计划时间')
  }
  const payload = {
    machine: form.value.machine,
    planned_start: form.value.range[0],
    planned_end: form.value.range[1],
    confirm: confirmed,
  }
  saving.value = true
  try {
    await doSchedule(payload)
  } catch (e) {
    const d = e.response?.data
    if (d?.need_confirm) {
      // 超容/机型不适配：人工确认后放行
      try {
        await ElMessageBox.confirm(
          d.warnings.join('\n') + '\n\n确认仍要排入该机台吗？',
          '排缸需人工确认',
          { type: 'warning', confirmButtonText: '仍要排入', cancelButtonText: '再想想' }
        )
        await doSchedule({ ...payload, confirm: true })
      } catch (cancelOrErr) {
        if (cancelOrErr?.response) ElMessage.error(cancelOrErr.response.data?.detail || '排缸失败')
      }
    } else if (d?.next_available) {
      ElMessage.error(`${d.detail}，可点击「使用此时段」改用推荐空档`)
    } else {
      ElMessage.error(d?.detail || '排缸失败')
    }
  } finally {
    saving.value = false
  }
}

async function unschedule(vat) {
  await api.unscheduleVat(vat.id)
  ElMessage.success('已取消排缸')
  load()
}

onMounted(load)
</script>

<style scoped>
.vat-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #e4e7ed; border-radius: 6px; margin-bottom: 8px; }
.vat-item.urgent { border-left: 4px solid #f56c6c; background: #fef0f0; }
.machine-card { min-height: 300px; }
.scheduled-item { border: 1px solid #e4e7ed; border-left: 4px solid #409eff; border-radius: 6px; padding: 10px; margin-bottom: 8px; }
.scheduled-item.producing { border-left-color: #e6a23c; background: #fdf6ec; }
.scheduled-item.has-warning { border-left-color: #f56c6c; background: #fef0f0; }
</style>
