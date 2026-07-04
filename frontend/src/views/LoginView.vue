<template>
  <div class="login-wrapper">
    <el-card class="login-card" shadow="always">
      <h2 style="text-align:center;margin-bottom:24px">图书馆AI助手</h2>

      <!-- 登录表单 -->
      <el-form v-if="!isRegister" ref="loginFormRef" :model="loginForm" :rules="loginRules" label-width="0" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="loginForm.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">登 录</el-button>
        </el-form-item>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else ref="registerFormRef" :model="registerForm" :rules="registerRules" label-width="0" @keyup.enter="handleRegister">
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="密码" size="large" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码" size="large" show-password :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleRegister">注 册</el-button>
        </el-form-item>
      </el-form>

      <!-- 切换登录/注册 -->
      <div style="text-align:center;margin-top:16px">
        <el-button text type="primary" @click="toggleMode">
          {{ isRegister ? '已有账号？返回登录' : '没有账号？立即注册' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { User, Lock } from "@element-plus/icons-vue"
import api from "../api/index.js"

const router = useRouter()
const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loading = ref(false)
const isRegister = ref(false)

// 登录表单
const loginForm = reactive({ username: "", password: "" })
const loginRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
}

// 注册表单
const registerForm = reactive({ username: "", password: "", confirmPassword: "" })
const registerRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 2, max: 20, message: "用户名长度在 2 到 20 个字符", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度不能少于 6 个字符", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请确认密码", trigger: "blur" },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error("两次输入的密码不一致"))
        } else {
          callback()
        }
      },
      trigger: "blur",
    },
  ],
}

// 切换登录/注册模式
const toggleMode = () => {
  isRegister.value = !isRegister.value
}

// 登录
const handleLogin = async () => {
  const valid = await loginFormRef.value.validate().catch(() => {})
  if (!valid) return
  loading.value = true
  try {
    const res = await api.post("/api/auth/login", loginForm)
    localStorage.setItem("token", res.data.access_token)

    // 获取用户信息并存储角色
    try {
      const userRes = await api.get("/api/auth/me")
      localStorage.setItem("userRole", userRes.data.role)
    } catch {
      // 获取用户信息失败，不影响登录
    }

    ElMessage.success("登录成功")
    router.push("/")
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || "登录失败")
  } finally {
    loading.value = false
  }
}

// 注册
const handleRegister = async () => {
  const valid = await registerFormRef.value.validate().catch(() => {})
  if (!valid) return
  loading.value = true
  try {
    await api.post("/api/auth/register", {
      username: registerForm.username,
      password: registerForm.password,
    })
    ElMessage.success("注册成功，请登录")
    // 切换回登录模式，并自动填充用户名
    loginForm.username = registerForm.username
    loginForm.password = ""
    registerForm.username = ""
    registerForm.password = ""
    registerForm.confirmPassword = ""
    isRegister.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || "注册失败")
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card { width: 400px; border-radius: 8px; }
</style>
