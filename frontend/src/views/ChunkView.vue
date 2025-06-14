<template>
  <div class="chunk-container">
    <!-- 左侧表单 -->
    <el-card class="chunk-form" title="分块设置">
      <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="选择文档" required>
          <el-select v-model="form.document" placeholder="请选择要分块的文档" style="width: 100%">
            <el-option
              v-for="doc in documents"
              :key="doc.filepath"
              :label="doc.filename"
              :value="doc.filepath"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="分块方法" required>
          <el-select 
            v-model="form.chunkMethod" 
            placeholder="请选择分块方法"
            @change="handleChunkMethodChange"
            style="width: 100%"
          >
            <el-option label="按页面分块" value="by_pages" />
            <el-option label="固定大小分块" value="fixed_size" />
            <el-option label="按段落分块" value="by_paragraphs" />
            <el-option label="按句子分块" value="by_sentences" />
          </el-select>
        </el-form-item>

        <el-form-item 
          v-if="form.chunkMethod === 'fixed_size'" 
          label="分块大小" 
          required
        >
          <el-input 
            v-model.number="form.chunkSize" 
            type="number" 
            placeholder="请输入分块大小（字符数）"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
            开始分块
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 右侧结果展示 -->
    <el-card class="chunk-result" title="分块结果">
      <div v-loading="loading" element-loading-text="正在分块中...">
        <pre v-if="result" class="result-content">{{ JSON.stringify(result, null, 2) }}</pre>
        <div v-else class="empty-result">
          请选择文档并设置分块方法
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 配置 axios 默认值
axios.defaults.baseURL = 'http://localhost:8000'

interface Document {
  filename: string
  filepath: string
}

const form = ref({
  document: '',
  chunkMethod: '',
  chunkSize: 1000
})

const documents = ref<Document[]>([])
const loading = ref(false)
const result = ref(null)

// 获取已加载的文档列表
const fetchDocuments = async () => {
  try {
    const response = await axios.get('/api/loaded-docs')
    documents.value = response.data
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  }
}

// 处理分块方法变化
const handleChunkMethodChange = (value: string) => {
  form.value.chunkMethod = value
}

// 处理分块提交
const handleSubmit = async () => {
  loading.value = true
  try {
    console.log('提交的数据:', form.value)  // 添加调试日志
    const response = await axios.post('/api/chunk', {
      doc_id: form.value.document,
      chunking_option: form.value.chunkMethod,
      chunk_size: form.value.chunkSize
    })
    result.value = response.data
    ElMessage.success('分块完成')
  } catch (error) {
    console.error('分块错误:', error)  // 添加错误日志
    ElMessage.error('分块失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.chunk-container {
  padding: 24px;
  display: flex;
  gap: 24px;
  height: 100%;
}

.chunk-form {
  width: 400px;
}

.chunk-result {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-content {
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.empty-result {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}
</style> 