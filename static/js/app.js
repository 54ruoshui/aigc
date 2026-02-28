// GraphRAG Web应用交互功能

// 全局变量
let currentGraph = null;
let simulation = null;
let isRecording = false;
let recognition = null;
let queryHistory = [];

// 初始化语音识别
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'zh-CN';

        recognition.onstart = function() {
            isRecording = true;
            updateVoiceButton();
            showMessage('正在聆听...', 'info');
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('questionInput').value = transcript;
            showMessage('识别成功: ' + transcript, 'success');
        };

        recognition.onerror = function(event) {
            console.error('语音识别错误:', event.error);
            showMessage('语音识别失败: ' + event.error, 'danger');
            isRecording = false;
            updateVoiceButton();
        };

        recognition.onend = function() {
            isRecording = false;
            updateVoiceButton();
        };
    } else {
        console.warn('浏览器不支持语音识别');
        document.getElementById('voiceBtn').style.display = 'none';
    }
}

// 更新语音按钮状态
function updateVoiceButton() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (isRecording) {
        voiceBtn.classList.add('recording');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
    } else {
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
}

// 切换语音识别
function toggleVoiceRecognition() {
    if (!recognition) {
        showMessage('您的浏览器不支持语音识别功能', 'warning');
        return;
    }

    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

// 加载查询历史
function loadQueryHistory() {
    const savedHistory = localStorage.getItem('graphrag_history');
    if (savedHistory) {
        queryHistory = JSON.parse(savedHistory);
        updateHistoryDisplay();
    }
}

// 保存查询历史
function saveQueryHistory() {
    localStorage.setItem('graphrag_history', JSON.stringify(queryHistory));
}

// 添加查询到历史记录
function addToHistory(question, answer, processingTime) {
    const historyItem = {
        question: question,
        answer: answer,
        processingTime: processingTime || 0,  // 确保processingTime不为undefined
        timestamp: new Date().toISOString()
    };
    
    queryHistory.unshift(historyItem);
    
    // 限制历史记录数量
    if (queryHistory.length > 20) {
        queryHistory = queryHistory.slice(0, 20);
    }
    
    saveQueryHistory();
    updateHistoryDisplay();
}

// 更新历史记录显示
function updateHistoryDisplay() {
    const historyContainer = document.getElementById('historyContainer');
    const historyList = document.getElementById('historyList');
    
    if (queryHistory.length === 0) {
        historyContainer.style.display = 'none';
        return;
    }
    
    historyContainer.style.display = 'block';
    historyList.innerHTML = '';
    
    queryHistory.forEach((item, index) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const date = new Date(item.timestamp);
        const timeString = date.toLocaleString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        historyItem.innerHTML = `
            <div class="history-question">${item.question}</div>
            <div class="history-time">${timeString} · ${item.processingTime ? item.processingTime.toFixed(2) + '秒' : '处理时间未知'}</div>
        `;
        
        historyItem.onclick = function() {
            document.getElementById('questionInput').value = item.question;
            submitQuery();
        };
        
        historyList.appendChild(historyItem);
    });
}

// 清空历史记录
function clearHistory() {
    if (confirm('确定要清空所有查询历史吗？')) {
        queryHistory = [];
        saveQueryHistory();
        updateHistoryDisplay();
        showMessage('历史记录已清空', 'success');
    }
}

// 显示消息提示
function showMessage(message, type = 'info') {
    const messageContainer = document.getElementById('messageContainer');
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    messageContainer.appendChild(alertDiv);
    
    // 自动消失
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 格式化答案 - 简化但更可靠的Markdown解析
function formatAnswer(answer) {
    if (!answer) return '';
    
    // 分行处理，保持原始结构
    const lines = answer.split('\n');
    const formattedLines = [];
    let inCodeBlock = false;
    let inList = false;
    let listType = null; // 'ordered' or 'unordered'
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        const trimmed = line.trim();
        
        // 处理代码块
        if (trimmed.startsWith('```')) {
            if (inCodeBlock) {
                formattedLines.push('</code></pre>');
                inCodeBlock = false;
            } else {
                formattedLines.push('<pre class="bg-light p-3 rounded"><code>');
                inCodeBlock = true;
            }
            continue;
        }
        
        if (inCodeBlock) {
            formattedLines.push(line);
            continue;
        }
        
        // 处理空行
        if (trimmed === '') {
            if (inList) {
                formattedLines.push(listType === 'ordered' ? '</ol>' : '</ul>');
                inList = false;
                listType = null;
            }
            formattedLines.push('<br>');
            continue;
        }
        
        // 处理标题
        if (trimmed.match(/^#{1,6}\s/)) {
            if (inList) {
                formattedLines.push(listType === 'ordered' ? '</ol>' : '</ul>');
                inList = false;
                listType = null;
            }
            
            const level = trimmed.match(/^(#+)/)[1].length;
            const title = trimmed.replace(/^#+\s/, '');
            formattedLines.push(`<h${Math.min(level + 2, 6)} class="mt-3 mb-2">${processInlineFormatting(title)}</h${Math.min(level + 2, 6)}>`);
            continue;
        }
        
        // 处理引用
        if (trimmed.startsWith('> ')) {
            if (inList) {
                formattedLines.push(listType === 'ordered' ? '</ol>' : '</ul>');
                inList = false;
                listType = null;
            }
            const quote = trimmed.replace(/^>\s/, '');
            formattedLines.push(`<blockquote class="border-left border-primary pl-3">${processInlineFormatting(quote)}</blockquote>`);
            continue;
        }
        
        // 处理有序列表
        if (trimmed.match(/^\d+\.\s/)) {
            if (!inList || listType !== 'ordered') {
                if (inList) formattedLines.push('</ul>');
                formattedLines.push('<ol class="mb-3">');
                inList = true;
                listType = 'ordered';
            }
            const item = trimmed.replace(/^\d+\.\s/, '');
            formattedLines.push(`<li>${processInlineFormatting(item)}</li>`);
            continue;
        }
        
        // 处理无序列表
        if (trimmed.match(/^[-*•]\s/)) {
            if (!inList || listType !== 'unordered') {
                if (inList) formattedLines.push('</ol>');
                formattedLines.push('<ul class="mb-3">');
                inList = true;
                listType = 'unordered';
            }
            const item = trimmed.replace(/^[-*•]\s/, '');
            formattedLines.push(`<li>${processInlineFormatting(item)}</li>`);
            continue;
        }
        
        // 处理普通段落
        if (inList) {
            formattedLines.push(listType === 'ordered' ? '</ol>' : '</ul>');
            inList = false;
            listType = null;
        }
        
        formattedLines.push(`<p class="mb-2">${processInlineFormatting(line)}</p>`);
    }
    
    // 关闭未关闭的列表
    if (inList) {
        formattedLines.push(listType === 'ordered' ? '</ol>' : '</ul>');
    }
    
    return formattedLines.join('');
}

// 处理行内格式化
function processInlineFormatting(text) {
    // 处理行内代码
    let formatted = text.replace(/`([^`]+)`/g, '<code class="bg-light px-1 rounded">$1</code>');
    
    // 处理删除线
    formatted = formatted.replace(/~~([^~\n]+)~~/g, '<del>$1</del>');
    
    // 处理加粗和斜体组合 - ***粗斜体***
    formatted = formatted.replace(/\*\*\*([^*\n]+)\*\*\*/g, '<strong><em>$1</em></strong>');
    
    // 处理加粗 - **粗体**
    formatted = formatted.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    
    // 处理下划线斜体 - __斜体__
    formatted = formatted.replace(/__([^_\n]+)__/g, '<em>$1</em>');
    
    // 处理星号斜体 - *斜体*
    // 使用更简单的方法，先替换所有可能的斜体，然后修复加粗的部分
    formatted = formatted.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
    
    // 修复被错误处理的加粗部分
    formatted = formatted.replace(/<strong><em>([^<]+)<\/em><\/strong>/g, '<strong>$1</strong>');
    
    // 处理链接
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-primary">$1</a>');
    
    return formatted;
}

// 复制答案到剪贴板
function copyAnswer() {
    const answerContent = document.getElementById('answerContent').textContent;
    navigator.clipboard.writeText(answerContent).then(() => {
        showMessage('答案已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showMessage('复制失败，请手动选择复制', 'danger');
    });
}

// 分享功能
function shareAnswer() {
    const question = document.querySelector('#answerContent .alert-info strong').textContent;
    const answer = document.getElementById('answerContent').textContent;
    const shareText = `问题：${question}\n答案：${answer}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'GraphRAG问答',
            text: shareText
        }).then(() => {
            showMessage('分享成功', 'success');
        }).catch(err => {
            console.error('分享失败:', err);
        });
    } else {
        // 降级到复制
        navigator.clipboard.writeText(shareText).then(() => {
            showMessage('内容已复制，您可以手动分享', 'success');
        });
    }
}

// 导出图谱为图片
function exportGraph() {
    if (!currentGraph) {
        showMessage('没有可导出的图谱', 'warning');
        return;
    }
    
    const svgElement = document.querySelector('#graph svg');
    if (!svgElement) {
        showMessage('图谱渲染失败', 'danger');
        return;
    }
    
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    canvas.width = svgElement.clientWidth;
    canvas.height = svgElement.clientHeight;
    
    img.onload = function() {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob(function(blob) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `graph_${Date.now()}.png`;
            a.click();
            URL.revokeObjectURL(url);
            showMessage('图谱已导出', 'success');
        });
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
}

// 键盘快捷键
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter 提交查询
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            submitQuery();
        }
        
        // Ctrl/Cmd + K 清空输入
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('questionInput').value = '';
            document.getElementById('questionInput').focus();
        }
        
        // Esc 停止语音识别
        if (e.key === 'Escape' && isRecording) {
            recognition.stop();
        }
    });
}

// 主题切换
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // 更新按钮图标
    const themeBtn = document.getElementById('themeBtn');
    if (newTheme === 'dark') {
        themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
    } else {
        themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
    }
}

// 加载主题
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    
    const themeBtn = document.getElementById('themeBtn');
    if (savedTheme === 'dark') {
        themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
    } else {
        themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
    }
}

// 全屏功能
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
        document.getElementById('fullscreenBtn').innerHTML = '<i class="fas fa-compress"></i>';
    } else {
        document.exitFullscreen();
        document.getElementById('fullscreenBtn').innerHTML = '<i class="fas fa-expand"></i>';
    }
}

// Neo4j风格图谱可视化
let neo4jGraph = null;
let performanceOptimizer = null;
let interactionEnhancer = null;

function displayEnhancedGraph(graphData) {
    if (!graphData || !graphData.nodes) {
        console.warn('图谱数据为空或格式不正确:', graphData);
        return;
    }

    // 更新统计信息
    const nodeCountElement = document.getElementById('nodeCount');
    const edgeCountElement = document.getElementById('edgeCount');
    const pathCountElement = document.getElementById('pathCount');
    
    if (nodeCountElement) nodeCountElement.textContent = graphData.nodes.length;
    if (edgeCountElement) edgeCountElement.textContent = graphData.relationships ? graphData.relationships.length : 0;
    if (pathCountElement) pathCountElement.textContent = graphData.paths ? graphData.paths.length : 0;

    // 初始化Neo4j风格图谱
    if (!neo4jGraph) {
        neo4jGraph = new Neo4jGraph('graph', {
            nodeRadius: 25,
            linkDistance: 100,
            chargeStrength: -400,
            fontSize: 12
        });
        
        // 初始化性能优化器
        performanceOptimizer = new GraphPerformanceOptimizer(neo4jGraph);
        
        // 初始化交互增强器
        interactionEnhancer = new GraphInteractionEnhancer(neo4jGraph);
    }

    // 更新图谱数据
    neo4jGraph.updateGraph(graphData);
    
    // 自动适应视图
    setTimeout(() => {
        neo4jGraph.zoomToFit();
    }, 500);
    
    // 显示成功消息
    showMessage(`已加载 ${graphData.nodes.length} 个节点和 ${graphData.relationships ? graphData.relationships.length : 0} 个关系`, 'success');
}

// 加载图统计信息
async function loadGraphStats() {
    try {
        const response = await fetch('/api/graph_stats');
        const stats = await response.json();
        const totalNodesElement = document.getElementById('totalNodes');
        if (totalNodesElement && stats.totalNodes) {
            totalNodesElement.textContent = stats.totalNodes;
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 设置搜索建议
function setupSearchSuggestions() {
    const input = document.getElementById('questionInput');
    const suggestions = document.getElementById('searchSuggestions');
    
    if (!input || !suggestions) {
        console.warn('搜索建议元素未找到');
        return;
    }
    
    input.addEventListener('input', async function() {
        const query = this.value.trim();
        if (query.length < 2) {
            suggestions.style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/api/search_nodes?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.nodes && data.nodes.length > 0) {
                suggestions.innerHTML = '';
                data.nodes.slice(0, 5).forEach(node => {
                    const item = document.createElement('div');
                    item.className = 'suggestion-item';
                    item.textContent = `${node.name} (${node.type})`;
                    item.onclick = () => {
                        input.value = `关于${node.name}的问题`;
                        suggestions.style.display = 'none';
                    };
                    suggestions.appendChild(item);
                });
                suggestions.style.display = 'block';
            } else {
                suggestions.style.display = 'none';
            }
        } catch (error) {
            console.error('搜索建议失败:', error);
        }
    });
    
    // 点击其他地方隐藏建议
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !suggestions.contains(e.target)) {
            suggestions.style.display = 'none';
        }
    });
}

// 提交查询
async function submitQuery() {
    const questionInputElement = document.getElementById('questionInput');
    if (!questionInputElement) {
        console.error('questionInput 元素未找到');
        return;
    }
    
    const question = questionInputElement.value.trim();
    if (!question) {
        alert('请输入您的问题');
        return;
    }

    // 显示加载状态
    const loadingElement = document.getElementById('loading');
    const answerCardElement = document.getElementById('answerCard');
    const searchSuggestionsElement = document.getElementById('searchSuggestions');
    
    if (loadingElement) loadingElement.style.display = 'block';
    if (answerCardElement) answerCardElement.style.display = 'none';
    if (searchSuggestionsElement) searchSuggestionsElement.style.display = 'none';

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();

        if (response.ok) {
            displayAnswer(data);
            if (typeof displayEnhancedGraph !== 'undefined') {
                displayEnhancedGraph(data.graph_data);
            } else {
                console.warn('displayEnhancedGraph 函数未定义');
            }
            
            // 添加到历史记录
            if (typeof addToHistory !== 'undefined') {
                addToHistory(data.question, data.answer, data.processing_time);
            }
        } else {
            throw new Error(data.error || '查询失败');
        }
    } catch (error) {
        console.error('查询失败:', error);
        const answerContentElement = document.getElementById('answerContent');
        if (answerContentElement) {
            answerContentElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${error.message || '查询失败，请稍后再试'}
                </div>
            `;
        }
        if (answerCardElement) answerCardElement.style.display = 'block';
    } finally {
        if (loadingElement) loadingElement.style.display = 'none';
    }
}

// 显示答案
function displayAnswer(data) {
    const answerContentElement = document.getElementById('answerContent');
    const processingTimeElement = document.getElementById('processingTime');
    const answerCardElement = document.getElementById('answerCard');
    
    if (!answerContentElement) {
        console.error('answerContent 元素未找到');
        return;
    }
    
    // 确保formatAnswer函数可用，如果不可用则等待加载
    const waitForFormatAnswer = (callback) => {
        if (typeof formatAnswer !== 'undefined') {
            callback();
        } else {
            setTimeout(() => waitForFormatAnswer(callback), 100);
        }
    };
    
    waitForFormatAnswer(() => {
        let formattedAnswer;
        if (typeof formatAnswer !== 'undefined') {
            formattedAnswer = formatAnswer(data.answer);
            console.log('使用formatAnswer函数格式化答案');
        } else {
            // 如果还是不可用，使用简单的格式化
            formattedAnswer = data.answer.replace(/\n/g, '<br>');
            console.warn('formatAnswer函数不可用，使用简单格式化');
        }
        
        answerContentElement.innerHTML = `
            <div class="alert alert-info">
                <strong>问题：</strong>${data.question}
            </div>
            <div class="mt-3 answer-content">
                ${formattedAnswer}
            </div>
        `;
        
        if (processingTimeElement) {
            processingTimeElement.textContent = data.processing_time !== undefined ? data.processing_time.toFixed(2) : '未知';
        }
        if (answerCardElement) {
            answerCardElement.style.display = 'block';
            // 添加显示动画
            answerCardElement.classList.add('fade-in');
        }
    });
}

// 示例问题点击
function askQuestion(question) {
    const questionInputElement = document.getElementById('questionInput');
    if (questionInputElement) {
        questionInputElement.value = question;
        submitQuery();
    } else {
        console.error('questionInput 元素未找到');
    }
}

// 处理回车键
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        submitQuery();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initSpeechRecognition();
    loadQueryHistory();
    loadTheme();
    setupKeyboardShortcuts();
    loadGraphStats();
    setupSearchSuggestions();
    
    // 添加加载动画
    document.body.classList.add('fade-in');
    
    // 检查浏览器兼容性
    checkBrowserCompatibility();
});

// 检查浏览器兼容性
function checkBrowserCompatibility() {
    const features = [
        { name: 'localStorage', check: () => typeof Storage !== 'undefined' },
        { name: 'Clipboard API', check: () => navigator.clipboard },
        { name: 'Web Share API', check: () => navigator.share },
        { name: 'Fullscreen API', check: () => document.documentElement.requestFullscreen },
        { name: 'Speech Recognition', check: () => 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window }
    ];
    
    const unsupported = features.filter(f => !f.check());
    
    if (unsupported.length > 0) {
        console.warn('您的浏览器不支持以下功能:', unsupported.map(f => f.name).join(', '));
    }
}

// Neo4j图谱控制函数
function resetZoom() {
    if (neo4jGraph) {
        neo4jGraph.resetZoom();
        showMessage('视图已重置', 'info');
    }
}

function fitToScreen() {
    if (neo4jGraph) {
        neo4jGraph.zoomToFit();
        showMessage('已适应屏幕', 'info');
    }
}

// 导出函数供HTML调用
window.toggleVoiceRecognition = toggleVoiceRecognition;
window.clearHistory = clearHistory;
window.copyAnswer = copyAnswer;
window.shareAnswer = shareAnswer;
window.exportGraph = exportGraph;
window.toggleTheme = toggleTheme;
window.toggleFullscreen = toggleFullscreen;
window.displayEnhancedGraph = displayEnhancedGraph;
window.resetZoom = resetZoom;
window.fitToScreen = fitToScreen;
window.formatAnswer = formatAnswer;
window.processInlineFormatting = processInlineFormatting;
window.loadGraphStats = loadGraphStats;
window.setupSearchSuggestions = setupSearchSuggestions;
window.askQuestion = askQuestion;
window.handleKeyPress = handleKeyPress;
window.submitQuery = submitQuery;
window.displayAnswer = displayAnswer;

// 确保页面加载完成后立即导出函数
document.addEventListener('DOMContentLoaded', function() {
    // 再次导出函数，确保可用
    window.formatAnswer = formatAnswer;
    window.processInlineFormatting = processInlineFormatting;
    console.log('formatAnswer函数已导出');
});