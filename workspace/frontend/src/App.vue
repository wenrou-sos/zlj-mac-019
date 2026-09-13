<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon :size="24" color="#fff"><Grid /></el-icon>
        <span>印染车间 MES</span>
      </div>
      <el-menu :default-active="$route.path" router background-color="#1f2d3d" text-color="#bfcbd9"
        active-text-color="#409eff" class="menu">
        <el-menu-item index="/"><el-icon><Monitor /></el-icon>生产仪表盘</el-menu-item>
        <el-menu-item index="/orders"><el-icon><Document /></el-icon>订单管理</el-menu-item>
        <el-menu-item index="/scheduling"><el-icon><Calendar /></el-icon>排缸安排</el-menu-item>
        <el-menu-item index="/progress"><el-icon><Loading /></el-icon>工序进度</el-menu-item>
        <el-menu-item index="/issues"><el-icon><Warning /></el-icon>质量异常</el-menu-item>
        <el-menu-item index="/reworks"><el-icon><RefreshLeft /></el-icon>返修跟踪</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ $route.meta.title }}</span>
        <span class="date">{{ today }}</span>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import dayjs from 'dayjs'
const today = dayjs().format('YYYY年MM月DD日')
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.layout { height: 100vh; }
.aside { background: #1f2d3d; }
.logo { display: flex; align-items: center; gap: 10px; padding: 18px 20px; color: #fff; font-size: 17px; font-weight: 600; }
.menu { border-right: none; }
.header { display: flex; justify-content: space-between; align-items: center; background: #fff; border-bottom: 1px solid #e4e7ed; }
.page-title { font-size: 17px; font-weight: 600; }
.date { color: #909399; font-size: 13px; }
.main { background: #f0f2f5; overflow-y: auto; }
.stat-card { text-align: center; }
.stat-num { font-size: 30px; font-weight: 700; margin-top: 8px; }
.stat-label { color: #909399; font-size: 13px; }
</style>
