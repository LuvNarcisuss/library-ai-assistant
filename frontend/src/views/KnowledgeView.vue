<template>
  <div style="padding:20px">
    <h3 style="margin:0 0 16px">知识库管理</h3>
    <div style="display:flex;gap:12px;margin-bottom:16px">
      <el-input v-model="search" placeholder="搜索名称/部门" clearable style="width:300px" @clear="fetchData" @keyup.enter="fetchData" />
      <el-button type="primary" @click="showDialog(null)">+ 新建知识库</el-button>
    </div>
    <el-table :data="items" v-loading="loading" stripe style="width:100%">
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="department" label="部门" width="120" />
      <el-table-column prop="owner" label="负责人" width="100" />
      <el-table-column prop="doc_count" label="文档数" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="showDialog(row)">编辑</el-button>
          <el-button text size="small" @click="handleClone(row)">克隆</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top:16px;text-align:right">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev,pager,next" @current-change="fetchData" />
    </div>

     <el-dialog v-model="dialogVisible" :title="editingId ? '编辑知识库' : '新建知识库'" width="500px">
      <el-form ref="formRef" :model="form" label-width="80px">
         <el-form-item label="名称" prop="name" :rules="[{ required: true, message: '请输入名称' }]">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="部门"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="form.owner" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import api from "../api/index.js"

const items = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(20); const loading = ref(false)
const search = ref("")
const dialogVisible = ref(false); const editingId = ref(null); const saving = ref(false)
const form = reactive({ name: "", description: "", department: "", owner: "" })
const formRef = ref(null)

const formatTime = (t) => t ? new Date(t).toLocaleString("zh-CN") : ""

const fetchData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (search.value) params.name = search.value
    const res = await api.get("/api/knowledge", { params })
    items.value = res.data.items; total.value = res.data.total
  } finally { loading.value = false }
}

const showDialog = (row) => {
  editingId.value = row ? row.id : null
  form.name = row?.name || ""
  form.description = row?.description || ""
  form.department = row?.department || ""
  form.owner = row?.owner || ""
  dialogVisible.value = true
}

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => {})
  if (!valid) return
  saving.value = true
  try {
    if (editingId.value) {
      await api.put(`/api/knowledge/${editingId.value}`, form)
      ElMessage.success("更新成功")
    } else {
      await api.post("/api/knowledge", form)
      ElMessage.success("创建成功")
    }
    dialogVisible.value = false
    fetchData()
  } catch (err) { ElMessage.error(err.response?.data?.detail || "操作失败") }
  finally { saving.value = false }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除知识库"${row.name}"？`, "警告", { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" })
  await api.delete(`/api/knowledge/${row.id}`)
  ElMessage.success("删除成功"); fetchData()
}

const handleClone = async (row) => {
  await api.post(`/api/knowledge/${row.id}/clone`)
  ElMessage.success("克隆成功"); fetchData()
}

onMounted(fetchData)
</script>
