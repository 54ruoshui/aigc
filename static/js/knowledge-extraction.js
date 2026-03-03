/**
 * 知识点提取功能JavaScript
 */

// 知识点提取相关函数
class KnowledgeExtractor {
    constructor() {
        this.maxContentLength = 10000;
        this.initEventListeners();
    }

    initEventListeners() {
        // 文件输入事件
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }

        // 内容输入事件
        const contentInput = document.getElementById('contentInput');
        if (contentInput) {
            contentInput.addEventListener('input', this.updateCharCount.bind(this));
        }

        // 拖拽上传事件
        const extractPanel = document.getElementById('extract-panel');
        if (extractPanel) {
            extractPanel.addEventListener('dragover', this.handleDragOver.bind(this));
            extractPanel.addEventListener('drop', this.handleFileDrop.bind(this));
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.readFile(file);
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.add('drag-over');
    }

    handleFileDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.readFile(files[0]);
        }
    }

    readFile(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const content = e.target.result;
            const contentInput = document.getElementById('contentInput');
            if (contentInput) {
                contentInput.value = content;
                this.updateCharCount();
            }
        };
        
        reader.onerror = () => {
            this.showMessage('文件读取失败', 'error');
        };
        
        // 根据文件类型选择读取方式
        if (file.type === 'application/pdf') {
            // PDF文件需要特殊处理
            this.showMessage('PDF文件处理功能正在开发中', 'warning');
        } else if (file.name.endsWith('.doc') || file.name.endsWith('.docx')) {
            // Word文档需要特殊处理
            this.showMessage('Word文档处理功能正在开发中', 'warning');
        } else {
            // 文本文件直接读取
            reader.readAsText(file);
        }
    }

    updateCharCount() {
        const contentInput = document.getElementById('contentInput');
        const charCount = document.getElementById('charCount');
        
        if (contentInput && charCount) {
            const count = contentInput.value.length;
            charCount.textContent = count;
            
            // 超过限制时显示警告
            if (count > this.maxContentLength) {
                charCount.classList.add('text-danger');
                contentInput.value = contentInput.value.substring(0, this.maxContentLength);
                charCount.textContent = this.maxContentLength;
            } else {
                charCount.classList.remove('text-danger');
            }
        }
    }

    async extractKnowledge() {
        const contentInput = document.getElementById('contentInput');
        const fileInput = document.getElementById('fileInput');
        const content = contentInput.value.trim();
        
        // 验证输入
        if (!content && !fileInput.files.length) {
            this.showMessage('请输入文档内容或上传文件', 'warning');
            return;
        }
        
        if (!content) {
            this.showMessage('请输入文档内容', 'warning');
            return;
        }
        
        if (content.length > this.maxContentLength) {
            this.showMessage(`内容过长，最多支持 ${this.maxContentLength} 字符`, 'warning');
            return;
        }
        
        // 显示加载状态
        this.showLoading(true);
        
        try {
            // 发送提取请求
            const response = await fetch('/api/extract_knowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayExtractionResult(result);
                this.showMessage(result.message, 'success');
            } else {
                this.showMessage(result.error || '提取失败', 'error');
            }
        } catch (error) {
            console.error('提取知识点失败:', error);
            this.showMessage('提取失败，请稍后再试', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async extractFromFile() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showMessage('请选择文件', 'warning');
            return;
        }
        
        // 验证文件类型
        const allowedTypes = ['text/plain', 'text/markdown', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        const allowedExtensions = ['.txt', '.md', '.doc', '.docx'];
        
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
            this.showMessage('不支持的文件类型', 'warning');
            return;
        }
        
        // 显示加载状态
        this.showLoading(true);
        
        try {
            // 创建FormData
            const formData = new FormData();
            formData.append('file', file);
            
            // 发送提取请求
            const response = await fetch('/api/extract_knowledge_file', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayExtractionResult(result);
                this.showMessage(result.message, 'success');
            } else {
                this.showMessage(result.error || '提取失败', 'error');
            }
        } catch (error) {
            console.error('文件提取失败:', error);
            this.showMessage('文件提取失败，请稍后再试', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const loading = document.getElementById('extractLoading');
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    displayExtractionResult(result) {
        // 显示结果卡片
        const resultCard = document.getElementById('extractResultCard');
        if (resultCard) {
            resultCard.style.display = 'block';
        }
        
        // 更新统计信息
        this.updateStats(result);
        
        // 显示关键字
        this.displayKeywords(result.keywords);
        
        // 显示关系
        this.displayRelationships(result.relationships);
        
        // 显示成功消息
        const successMessage = document.getElementById('extractSuccessMessage');
        const successText = document.getElementById('extractSuccessText');
        if (successMessage && successText) {
            successText.textContent = result.message;
            successMessage.style.display = 'block';
        }
        
        // 滚动到结果区域
        resultCard.scrollIntoView({ behavior: 'smooth' });
    }

    updateStats(result) {
        const keywordCount = document.getElementById('keywordCount');
        const relationshipCount = document.getElementById('relationshipCount');
        const nodeCreatedCount = document.getElementById('nodeCreatedCount');
        
        if (keywordCount) {
            keywordCount.textContent = result.keywords.length;
        }
        
        if (relationshipCount) {
            relationshipCount.textContent = result.relationships.length;
        }
        
        if (nodeCreatedCount && result.stats) {
            const created = result.stats.nodes_created || 0;
            const updated = result.stats.nodes_updated || 0;
            nodeCreatedCount.textContent = created + updated;
        }
    }

    displayKeywords(keywords) {
        const keywordsList = document.getElementById('keywordsList');
        if (!keywordsList) return;
        
        keywordsList.innerHTML = '';
        
        // 按类型分组
        const keywordsByType = {};
        keywords.forEach(kw => {
            if (!keywordsByType[kw.type]) {
                keywordsByType[kw.type] = [];
            }
            keywordsByType[kw.type].push(kw);
        });
        
        // 显示分组的关键字
        Object.keys(keywordsByType).forEach(type => {
            const typeDiv = document.createElement('div');
            typeDiv.className = 'keyword-type-group mb-3';
            
            const typeTitle = document.createElement('h6');
            typeTitle.className = 'text-primary';
            typeTitle.innerHTML = `<i class="fas fa-tag me-2"></i>${type}`;
            typeDiv.appendChild(typeTitle);
            
            const keywordItems = document.createElement('div');
            keywordItems.className = 'keyword-items';
            
            keywordsByType[type].forEach(kw => {
                const keywordItem = document.createElement('div');
                keywordItem.className = 'keyword-item';
                keywordItem.innerHTML = `
                    <span class="keyword-name">${kw.name}</span>
                    <span class="keyword-confidence">置信度: ${kw.confidence.toFixed(2)}</span>
                    ${kw.context ? `<div class="keyword-context">${kw.context.substring(0, 100)}...</div>` : ''}
                `;
                keywordItems.appendChild(keywordItem);
            });
            
            typeDiv.appendChild(keywordItems);
            keywordsList.appendChild(typeDiv);
        });
    }

    displayRelationships(relationships) {
        const relationshipsList = document.getElementById('relationshipsList');
        if (!relationshipsList) return;
        
        relationshipsList.innerHTML = '';
        
        relationships.forEach(rel => {
            const relItem = document.createElement('div');
            relItem.className = 'relationship-item';
            relItem.innerHTML = `
                <div class="relationship-content">
                    <span class="relationship-source">${rel.source.name}</span>
                    <span class="relationship-type">${rel.type}</span>
                    <span class="relationship-target">${rel.target.name}</span>
                    <span class="relationship-confidence">置信度: ${rel.confidence.toFixed(2)}</span>
                </div>
                ${rel.context ? `<div class="relationship-context">${rel.context.substring(0, 100)}...</div>` : ''}
            `;
            relationshipsList.appendChild(relItem);
        });
    }

    showMessage(message, type = 'info') {
        // 这里可以集成到现有的消息显示系统
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // 如果有全局的消息显示函数，使用它
        if (typeof window.showMessage === 'function') {
            window.showMessage(message, type);
        }
    }

    copyExtractionResult() {
        const resultCard = document.getElementById('extractResultCard');
        if (!resultCard) return;
        
        // 收集结果文本
        let resultText = '知识点提取结果\n\n';
        
        // 添加关键字
        const keywords = document.querySelectorAll('.keyword-item');
        if (keywords.length > 0) {
            resultText += '关键字:\n';
            keywords.forEach(item => {
                const name = item.querySelector('.keyword-name')?.textContent || '';
                const confidence = item.querySelector('.keyword-confidence')?.textContent || '';
                resultText += `- ${name} (${confidence})\n`;
            });
            resultText += '\n';
        }
        
        // 添加关系
        const relationships = document.querySelectorAll('.relationship-item');
        if (relationships.length > 0) {
            resultText += '关系:\n';
            relationships.forEach(item => {
                const source = item.querySelector('.relationship-source')?.textContent || '';
                const type = item.querySelector('.relationship-type')?.textContent || '';
                const target = item.querySelector('.relationship-target')?.textContent || '';
                const confidence = item.querySelector('.relationship-confidence')?.textContent || '';
                resultText += `- ${source} --[${type}]--> ${target} (${confidence})\n`;
            });
        }
        
        // 复制到剪贴板
        navigator.clipboard.writeText(resultText).then(() => {
            this.showMessage('结果已复制到剪贴板', 'success');
        }).catch(err => {
            console.error('复制失败:', err);
            this.showMessage('复制失败', 'error');
        });
    }

    exportExtractionResult() {
        const resultCard = document.getElementById('extractResultCard');
        if (!resultCard) return;
        
        // 创建JSON数据
        const exportData = {
            keywords: [],
            relationships: [],
            exportTime: new Date().toISOString()
        };
        
        // 收集关键字数据
        const keywords = document.querySelectorAll('.keyword-item');
        keywords.forEach(item => {
            const name = item.querySelector('.keyword-name')?.textContent || '';
            const confidence = item.querySelector('.keyword-confidence')?.textContent || '';
            exportData.keywords.push({
                name: name,
                confidence: parseFloat(confidence.split(': ')[1]) || 0
            });
        });
        
        // 收集关系数据
        const relationships = document.querySelectorAll('.relationship-item');
        relationships.forEach(item => {
            const source = item.querySelector('.relationship-source')?.textContent || '';
            const type = item.querySelector('.relationship-type')?.textContent || '';
            const target = item.querySelector('.relationship-target')?.textContent || '';
            const confidence = item.querySelector('.relationship-confidence')?.textContent || '';
            exportData.relationships.push({
                source: source,
                type: type,
                target: target,
                confidence: parseFloat(confidence.split(': ')[1]) || 0
            });
        });
        
        // 下载JSON文件
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `knowledge_extraction_${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showMessage('结果已导出', 'success');
    }
}

// 全局函数，供HTML调用
let knowledgeExtractor;

function extractKnowledge() {
    if (!knowledgeExtractor) {
        knowledgeExtractor = new KnowledgeExtractor();
    }
    knowledgeExtractor.extractKnowledge();
}

function copyExtractionResult() {
    if (!knowledgeExtractor) {
        knowledgeExtractor = new KnowledgeExtractor();
    }
    knowledgeExtractor.copyExtractionResult();
}

function exportExtractionResult() {
    if (!knowledgeExtractor) {
        knowledgeExtractor = new KnowledgeExtractor();
    }
    knowledgeExtractor.exportExtractionResult();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    knowledgeExtractor = new KnowledgeExtractor();
});