<template>
  <div class="parse-view">
    <div class="parse-container">
      <!-- 左侧控制面板 -->
      <div class="control-panel">
        <form @submit.prevent="handleParse" class="upload-form">
          <h2>PDF解析</h2>
          
          <!-- 文件上传 -->
          <div class="form-group">
            <label>选择PDF文件</label>
            <input 
              type="file" 
              @change="handleFileChange" 
              accept=".pdf"
              required
            >
          </div>

          <!-- 加载方法选择 -->
          <div class="form-group">
            <label>选择处理方法</label>
            <select v-model="selectedMethod" required>
              <option value="pymupdf">PyMuPDF</option>
              <option value="pypdf">PyPDF</option>
              <option value="pdfplumber">PDFPlumber</option>
              <option value="unstructured">Unstructured</option>
              <option value="pdfminer">PDFMiner</option>
            </select>
          </div>

          <!-- 解析方法选择 -->
          <div class="form-group">
            <label>解析方法</label>
            <select v-model="parseMethod" required>
              <option value="all_text">完整文本</option>
              <option value="by_pages">按页面</option>
              <option value="by_titles">按标题</option>
              <option value="text_and_tables">文本和表格</option>
            </select>
          </div>

          <template v-if="selectedMethod === 'unstructured'">
            <div class="form-group">
              <label>Strategy</label>
              <select v-model="strategy">
                <option value="auto">Auto</option>
                <option value="fast">Fast</option>
                <option value="hi_res">High Resolution</option>
              </select>
            </div>
          </template>

          <!-- 解析按钮 -->
          <button 
            type="submit" 
            :disabled="loading || !selectedFile"
          >
            {{ loading ? '处理中...' : 'PARSE' }}
          </button>
        </form>
      </div>

      <!-- 右侧结果展示 -->
      <div class="result-panel">
        <h2>解析结果</h2>
        <div v-if="loading" class="loading-mask">
          <div class="loading-spinner"></div>
        </div>
        <div v-else-if="error" class="error">
          {{ error }}
        </div>
        <div v-else-if="parseResult" class="result-content">
          <!-- 元数据展示 -->
          <div class="metadata-section">
            <h3>文档信息</h3>
            <div class="metadata-item">
              <span>文件名:</span>
              <span>{{ parseResult.metadata.filename }}</span>
            </div>
            <div class="metadata-item">
              <span>总页数:</span>
              <span>{{ parseResult.metadata.total_pages }}</span>
            </div>
            <div class="metadata-item">
              <span>解析方法:</span>
              <span>{{ parseResult.metadata.parsing_method }}</span>
            </div>
            <div class="metadata-item">
              <span>解析时间:</span>
              <span>{{ new Date(parseResult.metadata.timestamp).toLocaleString() }}</span>
            </div>
          </div>

          <!-- 内容展示 -->
          <div class="content-section">
            <h3>解析内容</h3>
            <div v-for="(item, index) in parseResult.content" :key="index" class="content-item">
              <div class="item-type">{{ item.type }}</div>
              <div class="item-content">
                <template v-if="item.type === 'table'">
                  <table class="result-table">
                    <tr v-for="(row, rowIndex) in item.rows" :key="rowIndex">
                      <td v-for="(cell, cellIndex) in row" :key="cellIndex">
                        {{ cell }}
                      </td>
                    </tr>
                  </table>
                </template>
                <template v-else>
                  {{ item.content }}
                </template>
              </div>
              <div class="item-page" v-if="item.page">页码: {{ item.page }}</div>
            </div>
          </div>
        </div>
        <div v-else class="no-result">
          请选择文件并点击PARSE按钮开始解析
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

// 设置axios默认baseURL
axios.defaults.baseURL = 'http://localhost:8000'

// 状态变量
const selectedFile = ref(null)
const selectedMethod = ref('pymupdf')
const parseMethod = ref('all_text')
const strategy = ref('auto')
const loading = ref(false)
const error = ref(null)
const parseResult = ref(null)

// 文件选择处理
const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    selectedFile.value = file
  } else {
    error.value = '请选择PDF文件'
    selectedFile.value = null
  }
}

// 解析处理
const handleParse = async (event) => {
  event.preventDefault() // 阻止表单默认提交
  
  if (!selectedFile.value) {
    error.value = '请先选择文件'
    return
  }

  loading.value = true
  error.value = null
  parseResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('loading_method', selectedMethod.value)
    formData.append('strategy', strategy.value)
    formData.append('chunking_strategy', parseMethod.value)
    formData.append('chunking_options', JSON.stringify({}))

    const response = await axios.post('/api/parse', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    parseResult.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || '解析失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.parse-view {
  padding: 20px;
  height: 100%;
}

.parse-container {
  display: flex;
  gap: 20px;
  height: 100%;
}

.control-panel {
  flex: 0 0 300px;
  padding: 20px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-panel {
  flex: 1;
  padding: 20px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow-y: auto;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 15px;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

button {
  width: 100%;
  padding: 12px;
  background-color: #1a237e;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
}

button:hover {
  background-color: #283593;
}

button:disabled {
  background-color: #9e9e9e;
  cursor: not-allowed;
}

.loading-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #1a237e;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  color: #f44336;
  padding: 20px;
  text-align: center;
}

.no-result {
  text-align: center;
  padding: 20px;
  color: #666;
}

.metadata-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.metadata-item {
  display: flex;
  margin-bottom: 8px;
}

.metadata-item span:first-child {
  flex: 0 0 100px;
  font-weight: bold;
}

.content-section {
  margin-top: 20px;
}

.content-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.item-type {
  font-weight: bold;
  color: #1a237e;
  margin-bottom: 8px;
}

.item-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.item-page {
  margin-top: 8px;
  font-size: 0.9em;
  color: #666;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.result-table td {
  border: 1px solid #ddd;
  padding: 8px;
}

h2 {
  margin-bottom: 20px;
  color: #333;
}

h3 {
  margin-bottom: 10px;
  color: #666;
}
</style> 