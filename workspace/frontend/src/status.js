// 状态 -> 展示文案/标签颜色 的公共映射
export const VAT_STATUS = {
  unscheduled: { text: '待排缸', type: 'info' },
  scheduled: { text: '已排缸', type: 'primary' },
  producing: { text: '生产中', type: 'warning' },
  inspecting: { text: '待检验', type: 'danger' },
  completed: { text: '已完成', type: 'success' },
}

export const ORDER_STATUS = {
  pending: { text: '待生产', type: 'info' },
  producing: { text: '生产中', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  shipped: { text: '已出货', type: 'primary' },
}

export const PRIORITY = {
  normal: { text: '普通', type: 'info' },
  urgent: { text: '加急', type: 'warning' },
  critical: { text: '特急', type: 'danger' },
}

export const STEP_STATUS = {
  not_started: { text: '未开始', type: 'info' },
  in_progress: { text: '进行中', type: 'warning' },
  done: { text: '已完成', type: 'success' },
  abnormal: { text: '异常', type: 'danger' },
}

export const ISSUE_STATUS = {
  open: { text: '待处理', type: 'danger' },
  processing: { text: '处理中', type: 'warning' },
  closed: { text: '已关闭', type: 'success' },
}

export const SEVERITY = {
  minor: { text: '轻微', type: 'info' },
  major: { text: '一般', type: 'warning' },
  critical: { text: '严重', type: 'danger' },
}

export const REWORK_STATUS = {
  pending: { text: '待处理', type: 'info' },
  processing: { text: '进行中', type: 'warning' },
  done: { text: '已完成', type: 'success' },
}

export const ISSUE_TYPES = [
  { value: 'color_diff', label: '色差' },
  { value: 'color_flower', label: '色花' },
  { value: 'stain', label: '沾污' },
  { value: 'fastness', label: '色牢度不合格' },
  { value: 'defect', label: '布面疵点' },
  { value: 'strength', label: '强力不足' },
  { value: 'other', label: '其他' },
]

export const REWORK_TYPES = [
  { value: 'redye', label: '复染' },
  { value: 'strip_redye', label: '剥色重染' },
  { value: 'resetting', label: '回修定型' },
  { value: 'rewash', label: '回洗' },
  { value: 'other', label: '其他' },
]
