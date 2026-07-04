<template>
  <div style="padding:20px">
    <h3 style="margin:0 0 20px">仪表盘</h3>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover"><div class="stat-card"><div class="stat-value">{{ stats.kbCount }}</div><div class="stat-label">知识库数</div></div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover"><div class="stat-card"><div class="stat-value">{{ stats.docCount }}</div><div class="stat-label">文档数</div></div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover"><div class="stat-card"><div class="stat-value">{{ stats.qaCount }}</div><div class="stat-label">总提问数</div></div></el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "../api/index.js"

const stats = ref({ kbCount: 0, docCount: 0, qaCount: 0 })

onMounted(async () => {
  try {
    const [kbRes, docRes, logRes] = await Promise.all([
      api.get("/api/knowledge", { params: { page: 1, page_size: 1 } }),
      api.get("/api/documents", { params: { page: 1, page_size: 1 } }),
      api.get("/api/logs", { params: { page: 1, page_size: 1 } }),
    ])
    stats.value = {
      kbCount: kbRes.data.total || 0,
      docCount: docRes.data.total || 0,
      qaCount: logRes.data.total || 0,
    }
  } catch (err) {
    console.error("Failed to load stats", err)
  }
})
</script>

<style scoped>
.stat-card { text-align: center; padding: 10px 0; }
.stat-value { font-size: 36px; font-weight: bold; color: #409EFF; }
.stat-label { font-size: 14px; color: #666; margin-top: 8px; }
</style>
