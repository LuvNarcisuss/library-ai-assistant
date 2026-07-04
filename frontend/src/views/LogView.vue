<template>
  <div style="padding:20px">
    <h3 style="margin:0 0 16px">对话日志</h3>
    <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:16px;align-items:center">
      <el-select v-model="filterKbId" placeholder="知识库" clearable style="width:180px" @change="fetchData">
        <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id" />
      </el-select>
      <el-input v-model="filterKeyword" placeholder="搜索关键词" clearable style="width:240px" @clear="fetchData" @keyup.enter="fetchData" />
    </div>
    <el-table :data="items" v-loading="loading" stripe style="width:100%">
      <el-table-column label="用户" width="120">
        <template #default="{ row }">{{ row.username || "-" }}</template>
      </el-table-column>
      <el-table-column label="问题" min-width="200">
        <template #default="{ row }">{{ truncate(row.question, 60) }}</template>
      </el-table-column>
      <el-table-column label="答案" min-width="300">
        <template #default="{ row }">{{ truncate(row.answer, 80) }}</template>
      </el-table-column>
      <el-table-column label="知识库" width="120">
        <template #default="{ row }">{{ row.knowledge_base_id || "-" }}</template>
      </el-table-column>
      <el-table-column label="时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top:16px;text-align:right">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev,pager,next" @current-change="fetchData" />
    </div>

    <el-dialog v-model="detailVisible" title="对话详情" width="700px">
      <div v-if="detailData">
        <div style="margin-bottom:12px;display:flex;align-items:center;gap:8px">
          <strong>用户：</strong>
          <el-tag size="small">{{ detailData.username || '未知用户' }}</el-tag>
          <span style="color:#999;font-size:12px">ID: {{ detailData.user_id || '-' }}</span>
        </div>
        <div style="margin-bottom:12px"><strong>问题：</strong></div>
        <div style="background:#f0f9eb;padding:10px 14px;border-radius:4px;margin-bottom:16px;line-height:1.5">{{ detailData.question }}</div>
        <div style="margin-bottom:12px"><strong>答案：</strong></div>
        <div style="background:#f0f2f5;padding:10px 14px;border-radius:4px;margin-bottom:16px;line-height:1.6;white-space:pre-wrap">{{ detailData.answer }}</div>
        <div v-if="detailData.sources" style="color:#999;font-size:13px">
          <strong>来源：</strong>{{ detailData.sources }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "../api/index.js"

const items = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(20); const loading = ref(false)
const filterKbId = ref(null); const filterKeyword = ref("")
const kbList = ref([])
const detailVisible = ref(false); const detailData = ref(null)

const truncate = (s, n) => s && s.length > n ? s.slice(0, n) + "..." : s || ""
const formatTime = (t) => t ? new Date(t).toLocaleString("zh-CN") : ""

const fetchData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterKbId.value) params.knowledge_base_id = filterKbId.value
    if (filterKeyword.value) params.keyword = filterKeyword.value
    const res = await api.get("/api/logs", { params })
    items.value = res.data.items; total.value = res.data.total
  } finally { loading.value = false }
}

const fetchKbList = async () => {
  try {
    const res = await api.get("/api/knowledge", { params: { page: 1, page_size: 100 } })
    kbList.value = res.data.items
  } catch { /* ignore */ }
}

const showDetail = (row) => {
  detailData.value = row
  detailVisible.value = true
}

onMounted(() => { fetchKbList(); fetchData() })
</script>
