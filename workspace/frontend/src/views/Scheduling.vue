<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="never">
          <template #header><b>待排缸（{{ unscheduled.length }}）</b></template>
          <div v-for="v in unscheduled" :key="v.id" class="vat-item">
            <div>
              <b>{{ v.vat_no }}</b>
              <el-tag size="small" style="margin-left: 6px">{{ v.color }}</el-tag>
              <div style="color: #909399; font-size: 12px; margin-top: 4px">
                {{ v.order_no }} · {{ v.weight_kg }} kg
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
              <div v-for="v in col.vats" :key="v.id" class="scheduled-item" :class="v.status">
                <div style="display: flex; justify-content: space-between">
                  <b>{{ v.vat_no }}</b>
                  <el-tag size="small" :type="VAT_STATUS[v.status]?.type">{{ v.status_display }}</el-tag>
                </div>
                <div style="color: #606266; font-size: 12px; margin-top: 4px">
                  {{ v.order_no }} · {{ v.color }} · {{ v.weight_kg }}kg
                </div>
                <div style="color: #909399; font-size: 12px; margin-top: 2px">
                  {{ v.planned_start }} ~ {{ v.planned_end }}
                </div>
                <el-button v-if="v.status === 'scheduled'" link type="danger" size="small" @click="unschedule(v)">取消排缸</el-button>
              </div>
              <el-empty v-if="!col.vats.length" description="空闲" :image-size="50" />
            </el-card>
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="`排缸 - ${current?.vat_no || ''}`" width="480px">
      <el-form label-width="90px">
        <el-form-item label="机台" required>
          <el-select v-model="form.machine" style="width: 100%">
            <el-option v-for="m in machines" :key="m.id" :label="`${m.name}（${m.machine_type_display} ${m.capacity_kg}kg）`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划时间" required>
          <el-date-picker v-model="form.range" type="datetimerange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确认排缸</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import api from '../api'
import { VAT_STATUS } from '../status'

const board = ref([])
const unscheduled = ref([])
const machines = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const current = ref(null)
const form = ref({ machine: null, range: null })

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
  // 预填：明天 08:00 ~ 18:00，便于直接微调
  const start = dayjs().add(1, 'day').hour(8).minute(0).second(0)
  form.value = {
    machine: null,
    range: [start.format('YYYY-MM-DDTHH:mm:ss'), start.add(10, 'hour').format('YYYY-MM-DDTHH:mm:ss')],
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.machine || !form.value.range || form.value.range.length !== 2) {
    return ElMessage.warning('请选择机台和计划时间')
  }
  saving.value = true
  try {
    await api.scheduleVat(current.value.id, {
      machine: form.value.machine,
      planned_start: form.value.range[0],
      planned_end: form.value.range[1],
    })
    ElMessage.success('排缸成功')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '排缸失败')
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
.machine-card { min-height: 300px; }
.scheduled-item { border: 1px solid #e4e7ed; border-left: 4px solid #409eff; border-radius: 6px; padding: 10px; margin-bottom: 8px; }
.scheduled-item.producing { border-left-color: #e6a23c; background: #fdf6ec; }
</style>
