<template>
  <div style="padding:20px">
    <h3 style="margin:0 0 16px">文档管理</h3>
    <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:16px;align-items:center">
      <el-select v-model="kbId" placeholder="选择知识库" style="width:240px" @change="fetchData">
        <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id" />
      </el-select>
      <el-upload v-if="kbId" :action="uploadUrlWithKb" :headers="headers" :on-success="onUploadSuccess" :on-error="onUploadError" :show-file-list="false" :accept="acceptedTypes" drag>
        <el-button type="primary" plain>点击上传或拖拽文件到此处</el-button>
      </el-upload>
    </div>
    <el-table :data="items" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="filename" label="文件名" min-width="200" />
      <el-table-column label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
      </el-table-column>
      <el-table-column prop="file_type" label="类型" width="80" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="chunk_count" label="文本块数" width="90" />
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click="handlePreview(row)">查看</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top:16px;text-align:right">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev,pager,next" @current-change="fetchData" />
    </div>

    <!-- 文档预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="`文档预览 - ${previewData.filename || ''}`"
      width="70%"
      top="5vh"
      destroy-on-close
    >
      <div v-loading="previewLoading" class="preview-container">
        <div v-if="previewData.chunks && previewData.chunks.length > 0" class="preview-content">
          <div class="preview-stats">
            <el-tag type="info" size="small">共 {{ previewData.chunk_count }} 个文本块</el-tag>
          </div>
          <div class="preview-chunks">
            <div v-for="(chunk, index) in previewData.chunks" :key="chunk.id || index" class="preview-chunk">
              <div class="chunk-header">
                <span class="chunk-index">文本块 {{ index + 1 }}</span>
                <span v-if="chunk.metadata?.chunk_index !== undefined" class="chunk-meta">
                  原始位置: {{ chunk.metadata.chunk_index }}
                </span>
              </div>
              <div class="chunk-content">{{ chunk.text }}</div>
            </div>
          </div>
        </div>
        <el-empty v-else-if="!previewLoading" description="暂无内容" />
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import api from "../api/index.js"

const items = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(20); const loading = ref(false)
const kbId = ref(null); const kbList = ref([])
const token = localStorage.getItem("token") || ""
const headers = computed(() => ({ Authorization: `Bearer ${token}` }))
const uploadUrl = "http://localhost:3680/api/documents/upload"
const uploadUrlWithKb = computed(() => `${uploadUrl}?knowledge_base_id=${kbId.value}`)
const acceptedTypes = ".txt,.pdf,.docx,.md"

// 预览相关状态
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewData = ref({
  filename: "",
  chunk_count: 0,
  chunks: []
})

const formatTime = (t) => t ? new Date(t).toLocaleString("zh-CN") : ""
const formatSize = (s) => { if (!s) return "0B"; const u = ["B","KB","MB","GB"]; let i=0; while(s>=1024 && i<3){s/=1024;i++} return s.toFixed(1)+u[i] }
const statusType = (s) => ({ pending: "info", processing: "primary", completed: "success", failed: "danger" }[s] || "info")

const fetchData = async () => {
  if (!kbId.value) return
  loading.value = true
  try {
    const res = await api.get("/api/documents", { params: { knowledge_base_id: kbId.value, page: page.value, page_size: pageSize.value } })
    items.value = res.data.items; total.value = res.data.total
  } finally { loading.value = false }
}

const fetchKbList = async () => {
  const res = await api.get("/api/knowledge", { params: { page: 1, page_size: 100 } })
  kbList.value = res.data.items
}

const onUploadSuccess = () => { ElMessage.success("上传成功"); fetchData() }
const onUploadError = (err) => { ElMessage.error(err.message || "上传失败") }

// 文档预览
const handlePreview = async (row) => {
  previewVisible.value = true
  previewLoading.value = true
  previewData.value = { filename: row.filename, chunk_count: 0, chunks: [] }

  try {
    const res = await api.get(`/api/documents/${row.id}/preview`)
    previewData.value = {
      filename: res.data.filename || row.filename,
      chunk_count: res.data.chunk_count || 0,
      chunks: res.data.chunks || []
    }
  } catch (error) {
    ElMessage.error("获取文档内容失败")
    console.error("预览失败:", error)
  } finally {
    previewLoading.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除"${row.filename}"？`, "警告", { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" })
  await api.delete(`/api/documents/${row.id}`)
  ElMessage.success("删除成功"); fetchData()
}

onMounted(fetchKbList)
</script>

<style scoped>
.preview-container {
  min-height: 200px;
  max-height: 60vh;
  overflow-y: auto;
}

.preview-content {
  padding: 0;
}

.preview-stats {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.preview-chunks {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-chunk {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
}

.chunk-index {
  font-weight: 600;
  color: #409eff;
  font-size: 13px;
}

.chunk-meta {
  font-size: 12px;
  color: #909399;
}

.chunk-content {
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fff;
}

/* 滚动条样式 */
.preview-container::-webkit-scrollbar {
  width: 6px;
}

.preview-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.preview-container::-webkit-scrollbar-track {
  background: #f2f6fc;
}
</style>
