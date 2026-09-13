import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('./views/Dashboard.vue'), meta: { title: '生产仪表盘' } },
  { path: '/orders', name: 'orders', component: () => import('./views/Orders.vue'), meta: { title: '订单管理' } },
  { path: '/orders/:id', name: 'order-detail', component: () => import('./views/OrderDetail.vue'), meta: { title: '订单详情' } },
  { path: '/scheduling', name: 'scheduling', component: () => import('./views/Scheduling.vue'), meta: { title: '排缸安排' } },
  { path: '/templates', name: 'templates', component: () => import('./views/Templates.vue'), meta: { title: '工艺模板' } },
  { path: '/progress', name: 'progress', component: () => import('./views/Progress.vue'), meta: { title: '工序进度' } },
  { path: '/issues', name: 'issues', component: () => import('./views/Issues.vue'), meta: { title: '质量异常' } },
  { path: '/reworks', name: 'reworks', component: () => import('./views/Reworks.vue'), meta: { title: '返修跟踪' } },
]

export default createRouter({ history: createWebHistory(), routes })
