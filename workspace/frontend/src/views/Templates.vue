<template>
  <div>
    <el-card shadow="never">
      <div style="display: flex; justify-content: space-between; margin-bottom: 16px">
        <span style="color: #909399; font-size: 13px">
          成熟工艺按布种+色号沉淀为模板，新缸号可直接套用；模板改动不影响已投产的缸号
        </span>
        <el-button type="primary" icon="Plus" @click="openForm()">新建模板</el-button>
      </div>

      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="name" label="模板名称" min-width="170" />
        <el-table-column prop="fabric_type" label="适用布种" width="140" />
        <el-table-column label="颜色/色号" width="130">
          <template #default="{ row }">{{ row.color || '—' }}<span v-if="row.color_no" style="color:#909399"> ({{ row.color_no }})</span></template>
        </el-table-column>
        <el-table-column prop="customer" label="客户确认样" width="160">
          <template #default="{ row }">{{ row.customer || '—' }}</template>
        </el-table-column>
        <el-table-column label="浴比" width="80" prop="bath_ratio" />
        <el-table-column label="温度" width="80">
          <template #default="{ row }">{{ row.dye_temp }}℃</template>
        </el-table-column>
        <el-table-column label="保温" width="80">
          <template #default="{ row }">{{ row.dye_time }}min</template>
        </el-table-column>
        <el-table-column label="pH" width="70" prop="ph_value" />
        <el-table-column label="染料/助剂" width="100" align="center">
          <template #default="{ row }">{{ row.dyes.length }} / {{ row.auxiliaries.length }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="130" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openForm(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑模板' : '新建模板'" width="680px">
      <el-form label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="模板名称" required><el-input v-model="form.name" placeholder="如 全棉针织-藏青N-2105" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用布种" required><el-input v-model="form.fabric_type" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="颜色"><el-input v-model="form.color" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="色号"><el-input v-model="form.color_no" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="客户确认样"><el-input v-model="form.customer" placeholder="确认样编号" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="浴比"><el-input v-model="form.bath_ratio" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="染色温度(℃)"><el-input-number v-model="form.dye_temp" :step="1" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="保温(min)"><el-input-number v-model="form.dye_time" :min="0" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="pH值"><el-input-number v-model="form.ph_value" :step="0.1" :min="0" :max="14" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="升温速率"><el-input-number v-model="form.heating_rate" :step="0.1" style="width: 100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="染料配方">
          <div v-for="(d, i) in form.dyes" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px; width: 100%">
            <el-input v-model="d.name" placeholder="染料名称" style="flex: 1" />
            <el-input-number v-model="d.pct" :step="0.1" :min="0" style="width: 130px" />
            <el-button link type="danger" icon="Delete" @click="form.dyes.splice(i, 1)" />
          </div>
          <el-button size="small" icon="Plus" @click="form.dyes.push({ name: '', pct: 0 })">加染料</el-button>
        </el-form-item>
        <el-form-item label="助剂">
          <div v-for="(a, i) in form.auxiliaries" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px; width: 100%">
            <el-input v-model="a.name" placeholder="助剂名称" style="flex: 1" />
            <el-input-number v-model="a.gpl" :step="0.1" :min="0" style="width: 130px" />
            <el-button link type="danger" icon="Delete" @click="form.auxiliaries.splice(i, 1)" />
          </div>
          <el-button size="small" icon="Plus" @click="form.auxiliaries.push({ name: '', gpl: 0 })">加助剂</el-button>
        </el-form-item>
        <el-form-item label="工艺备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const rows = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const blank = {
  name: '', fabric_type: '', color: '', color_no: '', customer: '',
  bath_ratio: '1:10', dye_temp: 98, dye_time: 40, ph_value: 7.0, heating_rate: 2.0,
  dyes: [], auxiliaries: [], note: '',
}
const form = ref({ ...blank })

async function load() {
  loading.value = true
  try {
    const res = await api.templates()
    rows.value = res.data
  } finally {
    loading.value = false
  }
}

function openForm(row) {
  form.value = row ? JSON.parse(JSON.stringify(row)) : { ...blank, dyes: [], auxiliaries: [] }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name || !form.value.fabric_type) return ElMessage.warning('模板名称和适用布种必填')
  saving.value = true
  try {
    if (form.value.id) await api.updateTemplate(form.value.id, form.value)
    else await api.createTemplate(form.value)
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data ? JSON.stringify(e.response.data) : '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除模板「${row.name}」？已套用该模板的缸号参数不受影响。`, '提示', { type: 'warning' })
  await api.deleteTemplate(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
