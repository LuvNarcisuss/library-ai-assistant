<template>
  <div class="chat-layout">
    <!-- 左侧会话列表 -->
    <div class="chat-sidebar">
      <div style="padding:12px;border-bottom:1px solid #e0e0e0;display:flex;gap:8px">
        <el-button size="small" type="primary" @click="newSession">+ 新建会话</el-button>
      </div>
      <el-menu :default-active="activeSession" @select="switchSession" style="border-right:none;overflow-y:auto;flex:1">
        <el-menu-item v-for="s in sessions" :key="s.session_id" :index="s.session_id" style="height:44px;position:relative">
          <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px">{{ s.title }}</span>
          <el-icon class="delete-btn" @click.stop="deleteSession(s.session_id)" style="position:absolute;right:8px;cursor:pointer;color:#999">
            <Delete />
          </el-icon>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-main" v-if="activeSession">
      <!-- 工具栏 -->
      <div style="padding:10px 16px;border-bottom:1px solid #e0e0e0;display:flex;align-items:center;gap:12px;background:#fafafa">
        <span style="font-size:13px;color:#666">知识库：</span>
        <el-select v-model="currentKbId" placeholder="选择知识库" size="small" style="width:200px" @change="fetchKbList">
          <el-option v-for="kb in kbList" :key="kb.id" :label="kb.name" :value="kb.id" />
        </el-select>
      </div>

      <!-- 消息列表 -->
      <div class="msg-list" ref="msgListRef">
        <div v-for="(msg, i) in messages" :key="i" style="margin-bottom:16px">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" style="display:flex;justify-content:flex-end;margin-bottom:4px">
            <div class="bubble-user">{{ msg.question }}</div>
          </div>
          <!-- 机器人消息 -->
          <div v-else style="display:flex;margin-bottom:4px">
            <div class="bubble-bot">
              <div v-html="renderMarkdown(msg.answer)" class="md-content"></div>
              <div v-if="msg.sources && msg.sources.length" style="margin-top:8px;font-size:12px;color:#999">
                <div v-for="(src, si) in msg.sources" :key="si" style="cursor:pointer;margin-bottom:2px" @click="showSource(src)">
                  📄 {{ src.filename }}（相似度: {{ (src.similarity * 100).toFixed(0) }}%）
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="loading" style="text-align:center;color:#999;padding:8px">正在思考...</div>
      </div>

      <!-- 快捷问题 -->
      <div v-if="showQuickQuestions" style="padding:8px 16px;display:flex;gap:8px;flex-wrap:wrap;border-top:1px solid #e0e0e0">
        <el-button v-for="(q, i) in quickQuestions" :key="i" size="small" text @click="sendQuick(q)">{{ q }}</el-button>
      </div>

      <!-- 输入区 -->
      <div class="chat-input">
        <el-input v-model="inputText" placeholder="输入问题，回车发送" @keyup.enter="sendMessage" :disabled="loading" />
        <el-button type="primary" @click="sendMessage" :loading="loading" :disabled="!inputText.trim()">发送</el-button>
      </div>
    </div>

    <!-- 无会话时提示 -->
    <div class="chat-main" v-else style="display:flex;align-items:center;justify-content:center;color:#999;font-size:16px">
      <div>请点击左侧「新建会话」开始提问</div>
    </div>

    <!-- 来源详情弹窗 -->
    <el-dialog v-model="sourceDialog.visible" title="来源详情" width="600px">
      <div style="margin-bottom:8px;color:#666;font-size:13px">文档：{{ sourceDialog.filename }}</div>
      <div style="background:#f5f7fa;padding:12px;border-radius:4px;font-size:14px;line-height:1.6;white-space:pre-wrap">{{ sourceDialog.snippet }}</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Delete } from "@element-plus/icons-vue"
import MarkdownIt from "markdown-it"
import api from "../api/index.js"

const md = new MarkdownIt({ html: true, linkify: true })
const renderMarkdown = (text) => md.render(text)

const sessions = ref([])
const activeSession = ref("")
const messages = ref([])
const inputText = ref("")
const loading = ref(false)
const currentKbId = ref(null)
const kbList = ref([])
const msgListRef = ref(null)
const showQuickQuestions = ref(true)

const sourceDialog = reactive({ visible: false, filename: "", snippet: "" })

const quickQuestions = [
  "本科生最多能借几本书？",
  "图书馆几点开门？",
  "怎么预约座位？",
  "校外怎么访问知网？",
]

// 加载会话列表
const loadSessions = async () => {
  try {
    const res = await api.get("/api/chat/sessions")
    sessions.value = res.data
  } catch { /* ignore */ }
}

// 切换会话
const switchSession = async (sessionId) => {
  activeSession.value = sessionId
  loading.value = true
  try {
    const res = await api.get(`/api/chat/sessions/${sessionId}`)
    const history = res.data.history || []

    // 将历史记录转换为消息格式（交替显示用户和助手消息）
    messages.value = []
    for (const record of history) {
      // 添加用户消息
      messages.value.push({
        role: "user",
        question: record.question,
        answer: ""
      })
      // 添加助手消息
      messages.value.push({
        role: "assistant",
        question: "",
        answer: record.answer,
        sources: record.sources || []
      })
    }

    showQuickQuestions.value = messages.value.length === 0

    // 设置当前知识库
    if (res.data.session?.knowledge_base_id) {
      currentKbId.value = res.data.session.knowledge_base_id
    }
  } catch {
    messages.value = []
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 新建会话
const newSession = async () => {
  try {
    // 创建新会话（后端会自动创建）
    const tempId = `session_${Date.now()}`
    activeSession.value = tempId
    messages.value = []
    showQuickQuestions.value = true

    // 加载知识库列表
    const kbRes = await api.get("/api/knowledge", { params: { page: 1, page_size: 100 } })
    kbList.value = kbRes.data.items
    if (kbList.value.length > 0 && !currentKbId.value) {
      currentKbId.value = kbList.value[0].id
    }
  } catch { /* ignore */ }
}

// 删除会话
const deleteSession = async (sessionId) => {
  try {
    await ElMessageBox.confirm("确定要删除这个会话吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    })

    await api.delete(`/api/chat/sessions/${sessionId}`)
    ElMessage.success("会话已删除")

    // 刷新会话列表
    await loadSessions()

    // 如果删除的是当前会话，清空聊天区域
    if (activeSession.value === sessionId) {
      activeSession.value = ""
      messages.value = []
    }
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error("删除失败")
    }
  }
}

// 加载知识库列表
const fetchKbList = async () => {
  try {
    const res = await api.get("/api/knowledge", { params: { page: 1, page_size: 100 } })
    kbList.value = res.data.items
  } catch { /* ignore */ }
}

// 发送消息
const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text) return
  if (!currentKbId.value && kbList.value.length > 0) {
    currentKbId.value = kbList.value[0].id
  }

  // 如果没有会话，先创建
  if (!activeSession.value) {
    activeSession.value = `session_${Date.now()}`
  }

  // 添加用户消息到界面
  messages.value.push({ role: "user", question: text, answer: "" })
  inputText.value = ""
  showQuickQuestions.value = false
  scrollToBottom()

  loading.value = true
  try {
    const res = await api.post("/api/chat", {
      question: text,
      session_id: activeSession.value,
      knowledge_base_id: currentKbId.value || undefined,
    })

    // 添加机器人回复
    messages.value.push({
      role: "assistant",
      question: "",
      answer: res.data.answer,
      sources: res.data.sources || [],
    })

    // 更新会话 ID（如果是新会话）
    if (activeSession.value !== res.data.session_id) {
      activeSession.value = res.data.session_id
    }

    // 刷新会话列表
    await loadSessions()
  } catch (err) {
    messages.value.push({ role: "assistant", question: "", answer: "请求失败，请重试", sources: [] })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const sendQuick = (q) => { inputText.value = q; sendMessage() }

const showSource = (src) => {
  sourceDialog.filename = src.filename
  sourceDialog.snippet = src.snippet || ""
  sourceDialog.visible = true
}

const scrollToBottom = async () => {
  await nextTick()
  if (msgListRef.value) {
    msgListRef.value.scrollTop = msgListRef.value.scrollHeight
  }
}

// 页面加载时获取会话列表
onMounted(async () => {
  await loadSessions()
  await fetchKbList()
})
</script>

<style scoped>
.chat-layout { display:flex;height:100%; }
.chat-sidebar { width:260px;border-right:1px solid #e4e7ed;display:flex;flex-direction:column;background:#fafafa;flex-shrink:0; }
.chat-main { flex:1;display:flex;flex-direction:column;overflow:hidden; }
.msg-list { flex:1;overflow-y:auto;padding:16px; }
.bubble-user { background:#409EFF;color:#fff;padding:10px 14px;border-radius:16px 16px 4px 16px;max-width:70%;word-wrap:break-word;line-height:1.5;font-size:14px; }
.bubble-bot { background:#f0f2f5;padding:10px 14px;border-radius:16px 16px 16px 4px;max-width:80%;word-wrap:break-word;line-height:1.6;font-size:14px; }
.md-content :deep(p) { margin:0 0 8px; }
.md-content :deep(p:last-child) { margin-bottom:0; }
.md-content :deep(ul), .md-content :deep(ol) { padding-left:20px;margin:4px 0; }
.chat-input { display:flex;padding:12px 16px;gap:8px;border-top:1px solid #e4e7ed;background:#fff; }
.chat-input .el-input { flex:1; }
.delete-btn { opacity:0;transition:opacity 0.2s; }
.el-menu-item:hover .delete-btn { opacity:1; }
</style>
