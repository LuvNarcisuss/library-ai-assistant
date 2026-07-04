<template>
  <div id="app" v-if="!isLoginPage" style="display:flex;height:100vh;width:100vw;overflow:hidden">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background:#304156;color:#fff;display:flex;flex-direction:column;height:100vh;flex-shrink:0">
      <div style="height:60px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:bold;border-bottom:1px solid rgba(255,255,255,.1)">图书馆AI助手</div>
      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF" style="border-right:none;flex:1;overflow-y:auto">
        <!-- 管理员菜单 -->
        <template v-if="userInfo?.role === 'admin'">
          <el-menu-item index="/"><el-icon><DataBoard /></el-icon><span>仪表盘</span></el-menu-item>
          <el-menu-item index="/knowledge"><el-icon><Folder /></el-icon><span>知识库管理</span></el-menu-item>
          <el-menu-item index="/documents"><el-icon><Document /></el-icon><span>文档管理</span></el-menu-item>
          <el-menu-item index="/chat"><el-icon><ChatDotSquare /></el-icon><span>智能问答</span></el-menu-item>
          <el-menu-item index="/logs"><el-icon><List /></el-icon><span>对话日志</span></el-menu-item>
        </template>
        <!-- 普通用户菜单 -->
        <template v-else>
          <el-menu-item index="/chat"><el-icon><ChatDotSquare /></el-icon><span>智能问答</span></el-menu-item>
        </template>
      </el-menu>
      <!-- 用户信息区域 -->
      <div style="border-top:1px solid rgba(255,255,255,.1);padding:12px">
        <el-popover placement="right" :width="220" trigger="click">
          <template #reference>
            <div style="display:flex;align-items:center;cursor:pointer;padding:8px;border-radius:4px;transition:background .2s" @mouseenter="$event.target.style.background='rgba(255,255,255,.1)'" @mouseleave="$event.target.style.background='transparent'">
              <el-avatar :size="36" style="background:#409EFF;flex-shrink:0">
                <el-icon :size="20"><User /></el-icon>
              </el-avatar>
              <div style="margin-left:10px;overflow:hidden">
                <div style="font-size:14px;font-weight:500;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ userInfo?.username || '未登录' }}</div>
                <div style="font-size:11px;color:#bfcbd9;margin-top:2px">点击查看详情</div>
              </div>
            </div>
          </template>
          <div style="padding:4px 0">
            <div style="text-align:center;padding:16px 0 12px;border-bottom:1px solid #eee">
              <el-avatar :size="64" style="background:#409EFF;margin-bottom:12px">
                <el-icon :size="32"><User /></el-icon>
              </el-avatar>
              <div style="font-size:16px;font-weight:600;color:#303133">{{ userInfo?.username || '未知用户' }}</div>
              <div style="font-size:12px;color:#909399;margin-top:4px">用户ID: {{ userInfo?.id || '-' }}</div>
            </div>
            <div style="padding:12px 0">
              <div style="display:flex;align-items:center;padding:8px 12px;color:#606266;font-size:14px">
                <el-icon style="margin-right:8px;color:#909399"><User /></el-icon>
                <span>用户名：</span>
                <span style="margin-left:auto;color:#303133">{{ userInfo?.username || '-' }}</span>
              </div>
              <div style="display:flex;align-items:center;padding:8px 12px;color:#606266;font-size:14px">
                <el-icon style="margin-right:8px;color:#909399"><UserFilled /></el-icon>
                <span>角色：</span>
                <span style="margin-left:auto;color:#303133">{{ userInfo?.role === 'admin' ? '管理员' : '普通用户' }}</span>
              </div>
              <div style="display:flex;align-items:center;padding:8px 12px;color:#606266;font-size:14px">
                <el-icon style="margin-right:8px;color:#909399"><Clock /></el-icon>
                <span>注册时间：</span>
                <span style="margin-left:auto;color:#303133">{{ formatTime(userInfo?.created_at) }}</span>
              </div>
            </div>
            <div style="border-top:1px solid #eee;padding-top:8px">
              <el-button type="danger" text style="width:100%;justify-content:center" @click="logout">
                <el-icon style="margin-right:4px"><SwitchButton /></el-icon>
                退出登录
              </el-button>
            </div>
          </div>
        </el-popover>
      </div>
    </el-aside>
    <!-- 内容区 -->
    <el-main style="background:#f0f2f5;padding:0;overflow-y:auto;flex:1;margin:0">
      <router-view />
    </el-main>
  </div>
  <router-view v-else />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataBoard, Folder, Document, ChatDotSquare, List, User, UserFilled, Clock, SwitchButton } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import api from './api/index.js'

const route = useRoute()
const router = useRouter()
const isLoginPage = computed(() => route.name === 'login')
const userInfo = ref(null)

// 获取用户信息
const fetchUserInfo = async () => {
  // 没有token时不请求
  const token = localStorage.getItem('token')
  if (!token) return

  try {
    const res = await api.get('/api/auth/me')
    userInfo.value = res.data
    // 同步更新 localStorage 中的角色信息
    localStorage.setItem('userRole', res.data.role)
  } catch (err) {
    console.error('获取用户信息失败:', err)
    // token无效时清除
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// 退出登录
const logout = async () => {
  await ElMessageBox.confirm('确定退出登录？', '提示')
  localStorage.removeItem('token')
  localStorage.removeItem('userRole')
  router.push('/login')
}

onMounted(() => {
  fetchUserInfo()
})
</script>
 <style>
 html, body { height: 100%; margin: 0; padding: 0; overflow: hidden; }
 #app { height: 100vh; width: 100vw; margin: 0; padding: 0; }
 </style>
