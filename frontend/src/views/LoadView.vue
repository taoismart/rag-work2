<template>
  <div class="load-view">
    <div class="form-container">
      <form @submit.prevent="handleSubmit" class="upload-form">
        <div class="form-group">
          <label>选择PDF文件</label>
          <input 
            type="file" 
            @change="handleFileChange" 
            accept=".pdf"
            required
          >
        </div>

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

        <template v-if="selectedMethod === 'unstructured'">
          <div class="form-group">
            <label>Strategy</label>
            <select v-model="strategy">
              <option value="auto">Auto</option>
              <option value="fast">Fast</option>
              <option value="hi_res">High Resolution</option>
            </select>
          </div>

          <div class="form-group">
            <label>Chunking Strategy</label>
            <select v-model="chunkingStrategy">
              <option value="basic">Basic</option>
              <option value="by_title">By Title</option>
              <option value="by_section">By Section</option>
            </select>
          </div>

          <div class="form-group">
            <label>Chunking Options</label>
            <textarea 
              v-model="chunkingOptions" 
              placeholder="输入JSON格式的选项，例如：{'chunk_size': 1000}"
            ></textarea>
          </div>
        </template>

        <button type="submit" :disabled="loading">
          {{ loading ? '处理中...' : '加载' }}
        </button>
      </form>
    </div>

    <div class="result-container" v-if="result">
      <pre>{{ JSON.stringify(result, null, 2) }}</pre>
    </div>

    <!-- 加载遮罩 -->
    <div class="loading-mask" v-if="loading">
      <div class="loading-spinner"></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const selectedMethod = ref('pymupdf')
const strategy = ref('auto')
const chunkingStrategy = ref('basic')
const chunkingOptions = ref('')
const loading = ref(false)
const result = ref(null)

const handleFileChange = (event) => {
  // 可以在这里添加文件类型和大小的验证
}

const handleSubmit = async () => {
  try {
    loading.value = true
    const formData = new FormData()
    const fileInput = document.querySelector('input[type="file"]')
    formData.append('file', fileInput.files[0])
    formData.append('loading_method', selectedMethod.value)
    
    if (selectedMethod.value === 'unstructured') {
      formData.append('strategy', strategy.value)
      formData.append('chunking_strategy', chunkingStrategy.value)
      if (chunkingOptions.value) {
        formData.append('chunking_options', chunkingOptions.value)
      }
    }

    const response = await axios.post('http://localhost:8000/api/load', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    result.value = response.data
  } catch (error) {
    console.error('Error:', error)
    alert('处理失败：' + error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.load-view {
  display: flex;
  gap: 20px;
  padding: 20px;
  height: 100%;
}

.form-container {
  width: 300px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group textarea {
  height: 100px;
  resize: vertical;
}

button {
  padding: 10px;
  background: #1a237e;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:disabled {
  background: #9e9e9e;
  cursor: not-allowed;
}

.result-container {
  flex: 1;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: auto;
}

.result-container pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
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
</style> 