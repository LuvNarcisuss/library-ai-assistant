import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", name: "home", component: () => import("../views/HomeView.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
    { path: "/login", name: "login", component: () => import("../views/LoginView.vue") },
    { path: "/knowledge", name: "knowledge", component: () => import("../views/KnowledgeView.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
    { path: "/documents", name: "documents", component: () => import("../views/DocumentView.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
    { path: "/chat", name: "chat", component: () => import("../views/ChatView.vue"), meta: { requiresAuth: true } },
    { path: "/logs", name: "logs", component: () => import("../views/LogView.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  ],
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token")
  const userRole = localStorage.getItem("userRole")

  // 未登录时跳转到登录页
  if (to.meta.requiresAuth && !token) {
    next("/login")
  }
  // 已登录时跳转到登录页，重定向到首页
  else if (to.name === "login" && token) {
    next("/")
  }
  // 需要管理员权限但用户不是管理员
  else if (to.meta.requiresAdmin && userRole !== "admin") {
    next("/chat")
  }
  else {
    next()
  }
})

export default router
