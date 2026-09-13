import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 10000 })

export default {
  // 仪表盘
  dashboard: () => api.get('/dashboard/'),
  // 订单
  orders: (params) => api.get('/orders/', { params }),
  order: (id) => api.get(`/orders/${id}/`),
  createOrder: (data) => api.post('/orders/', data),
  updateOrder: (id, data) => api.put(`/orders/${id}/`, data),
  // 机台
  machines: () => api.get('/machines/'),
  machineBoard: () => api.get('/machines/board/'),
  // 缸号
  vats: (params) => api.get('/vats/', { params }),
  vat: (id) => api.get(`/vats/${id}/`),
  createVat: (data) => api.post('/vats/', data),
  updateVat: (id, data) => api.patch(`/vats/${id}/`, data),
  scheduleVat: (id, data) => api.post(`/vats/${id}/schedule/`, data),
  scheduleCheck: (id, data) => api.post(`/vats/${id}/schedule_check/`, data),
  unscheduleVat: (id) => api.post(`/vats/${id}/unschedule/`),
  applyTemplate: (id, template) => api.post(`/vats/${id}/apply_template/`, { template }),
  copyParams: (id, source) => api.post(`/vats/${id}/copy_params/`, { source }),
  // 工艺模板
  templates: () => api.get('/templates/'),
  createTemplate: (data) => api.post('/templates/', data),
  updateTemplate: (id, data) => api.put(`/templates/${id}/`, data),
  deleteTemplate: (id) => api.delete(`/templates/${id}/`),
  // 工艺参数
  updateParams: (id, data) => api.put(`/params/${id}/`, data),
  // 工序
  advanceStep: (id, operator) => api.post(`/steps/${id}/advance/`, { operator }),
  abnormalStep: (id) => api.post(`/steps/${id}/mark_abnormal/`),
  // 质量异常
  issues: (params) => api.get('/issues/', { params }),
  createIssue: (data) => api.post('/issues/', data),
  transitionIssue: (id, status) => api.post(`/issues/${id}/transition/`, { status }),
  // 返修
  reworks: () => api.get('/reworks/'),
  createRework: (data) => api.post('/reworks/', data),
  updateRework: (id, data) => api.patch(`/reworks/${id}/`, data),
  finishRework: (id, result) => api.post(`/reworks/${id}/finish/`, { result }),
}
