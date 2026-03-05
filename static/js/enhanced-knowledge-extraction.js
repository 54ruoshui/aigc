/**
 * 增强版知识点提取JavaScript模块 - 支持技能验证
 */

class EnhancedKnowledgeExtraction {
    constructor() {
        this.config = null;
        this.validationEnabled = false;
        this.init();
    }

    async init() {
        try {
            // 获取配置
            const response = await fetch('/api/config');
            this.config = await response.json();
            
            // 检查技能验证是否启用
            this.validationEnabled = this.config.features.skill_validation;
            
            // 初始化UI
            this.setupUI();
            
            console.log('增强版知识点提取模块初始化完成');
            console.log('技能验证状态:', this.validationEnabled ? '启用' : '禁用');
            
        } catch (error) {
            console.error('初始化失败:', error);
            this.showError('初始化失败，请刷新页面重试');
        }
    }

    setupUI() {
        // 设置提取按钮
        const extractBtn = document.getElementById('extract-btn');
        if (extractBtn) {
            extractBtn.addEventListener('click', () => this.extractKnowledge());
        }

        // 设置文件上传
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // 设置验证选项
        this.setupValidationOptions();
        
        // 设置反馈功能
        this.setupFeedbackFeatures();
        
        // 设置验证统计显示
        this.setupValidationStats();
    }

    setupValidationOptions() {
        if (!this.validationEnabled) {
            // 如果验证未启用，隐藏相关UI元素
            const validationElements = document.querySelectorAll('.validation-only');
            validationElements.forEach(el => el.style.display = 'none');
            return;
        }

        // 验证开关已在HTML中定义，不需要重复创建
        // 只需确保验证开关的可见性
        const validationToggle = document.querySelector('.validation-toggle');
        if (validationToggle) {
            validationToggle.style.display = 'flex';
        }
    }

    setupFeedbackFeatures() {
        if (!this.validationEnabled) return;

        // 反馈区域会在displayResults方法中动态添加到结果中
        // 这里不需要预先创建，避免重复
    }

    setupValidationStats() {
        if (!this.validationEnabled) return;

        // 验证统计区域已在HTML中定义，不需要重复创建
        // 只需确保统计区域的可见性并绑定事件
        const validationStats = document.querySelector('.validation-stats');
        if (validationStats) {
            validationStats.style.display = 'block';
            
            // 绑定刷新统计事件（如果尚未绑定）
            const refreshBtn = document.getElementById('refresh-stats');
            if (refreshBtn && !refreshBtn.hasAttribute('data-listener')) {
                refreshBtn.setAttribute('data-listener', 'true');
                refreshBtn.addEventListener('click', () => {
                    this.loadValidationStats();
                });
                
                // 初始加载统计
                this.loadValidationStats();
            }
        }
    }

    bindFeedbackEvents() {
        const correctBtn = document.getElementById('feedback-correct');
        const partialBtn = document.getElementById('feedback-partial');
        const incorrectBtn = document.getElementById('feedback-incorrect');
        const submitBtn = document.getElementById('submit-feedback');
        const feedbackForm = document.querySelector('.feedback-form');

        correctBtn.addEventListener('click', () => {
            this.submitFeedback('all_correct');
        });

        partialBtn.addEventListener('click', () => {
            feedbackForm.style.display = 'block';
        });

        incorrectBtn.addEventListener('click', () => {
            feedbackForm.style.display = 'block';
        });

        submitBtn.addEventListener('click', () => {
            const correction = document.getElementById('feedback-correction').value;
            this.submitFeedback('needs_correction', correction);
            feedbackForm.style.display = 'none';
            document.getElementById('feedback-correction').value = '';
        });
    }

    async extractKnowledge() {
        const content = document.getElementById('content-input').value.trim();
        if (!content) {
            this.showError('请输入要提取的内容');
            return;
        }

        // 检查是否使用验证
        const useValidation = this.validationEnabled && 
                             document.getElementById('use-validation')?.checked !== false;

        // 显示加载状态
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/extract_knowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    use_validation: useValidation
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result);
                if (this.validationEnabled) {
                    this.loadValidationStats();
                }
            } else {
                this.showError(result.message || '提取失败');
            }
        } catch (error) {
            console.error('提取失败:', error);
            this.showError('提取失败，请稍后重试');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(result) {
        const resultsContainer = document.getElementById('extraction-results');
        const resultsCard = document.getElementById('results-card');
        
        // 构建结果HTML
        let html = `
            <div class="extraction-summary">
                <h4><i class="fas fa-info-circle me-2"></i>提取摘要</h4>
                <div class="summary-info">
                    <p><i class="fas fa-cog me-2"></i><strong>模式:</strong> ${this.getExtractionModeText(result.extraction_mode)}</p>
                    <p><i class="fas fa-file-alt me-2"></i><strong>摘要:</strong> ${result.summary}</p>
                    <p><i class="fas fa-comment me-2"></i><strong>消息:</strong> ${result.message}</p>
                    ${result.explanation ? `<p class="explanation"><i class="fas fa-lightbulb me-2"></i><strong>说明:</strong> ${result.explanation}</p>` : ''}
                </div>
            </div>
        `;

        // 显示统计信息
        if (result.stats) {
            html += this.buildStatsHTML(result.stats);
        }

        // 显示验证统计
        if (result.validation_stats) {
            html += this.buildValidationStatsHTML(result.validation_stats);
        }

        // 显示关键词
        if (result.keywords && result.keywords.length > 0) {
            html += this.buildKeywordsHTML(result);
        }

        // 显示关系
        if (result.relationships && result.relationships.length > 0) {
            html += this.buildRelationshipsHTML(result);
        }

        // 如果启用了验证，添加反馈区域
        if (this.validationEnabled) {
            html += `
                <div class="feedback-section validation-only">
                    <h4>反馈与改进</h4>
                    <p>帮助系统学习，提高提取质量</p>
                    <div class="feedback-buttons">
                        <button class="btn btn-success" id="feedback-correct">全部正确</button>
                        <button class="btn btn-warning" id="feedback-partial">部分正确</button>
                        <button class="btn btn-danger" id="feedback-incorrect">需要修正</button>
                    </div>
                    <div class="feedback-form" style="display: none;">
                        <textarea id="feedback-correction" placeholder="请描述需要修正的内容..."></textarea>
                        <button class="btn btn-primary" id="submit-feedback">提交反馈</button>
                    </div>
                </div>
            `;
        }

        resultsContainer.innerHTML = html;
        
        // 显示结果卡片并添加动画效果
        if (resultsCard) {
            resultsCard.classList.add('show');
        }
        
        // 绑定反馈事件（因为DOM已更新）
        if (this.validationEnabled) {
            this.bindFeedbackEvents();
        }
    }

    getExtractionModeText(mode) {
        switch (mode) {
            case 'enhanced_with_validation':
                return '增强版（带技能验证）';
            case 'basic':
                return '基础版';
            default:
                return '未知模式';
        }
    }

    buildStatsHTML(stats) {
        return `
            <div class="stats-section">
                <h4><i class="fas fa-chart-bar me-2"></i>统计信息</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-label"><i class="fas fa-plus-circle me-1"></i>创建节点:</span>
                        <span class="stat-value">${stats.nodes_created || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label"><i class="fas fa-edit me-1"></i>更新节点:</span>
                        <span class="stat-value">${stats.nodes_updated || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label"><i class="fas fa-link me-1"></i>创建关系:</span>
                        <span class="stat-value">${stats.relationships_created || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label"><i class="fas fa-exclamation-triangle me-1"></i>错误数:</span>
                        <span class="stat-value">${stats.errors || 0}</span>
                    </div>
                </div>
            </div>
        `;
    }

    buildValidationStatsHTML(validationStats) {
        if (!this.validationEnabled) return '';

        return `
            <div class="validation-section validation-only">
                <h4><i class="fas fa-check-circle me-2"></i>验证结果</h4>
                <div class="validation-grid">
                    <div class="validation-item">
                        <span class="validation-label"><i class="fas fa-percentage me-1"></i>验证通过率:</span>
                        <span class="validation-value">${(validationStats.validity_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div class="validation-item">
                        <span class="validation-label"><i class="fas fa-tally me-1"></i>总验证数:</span>
                        <span class="validation-value">${validationStats.total_validations || 0}</span>
                    </div>
                    <div class="validation-item">
                        <span class="validation-label"><i class="fas fa-chart-line me-1"></i>平均置信度:</span>
                        <span class="validation-value">${(validationStats.average_confidence || 0).toFixed(2)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    buildKeywordsHTML(result) {
        const keywords = result.keywords;
        const validKeywords = result.valid_keywords || [];
        
        let html = `
            <div class="keywords-section">
                <h4><i class="fas fa-tags me-2"></i>提取的关键词 (${keywords.length})</h4>
                <div class="keywords-list">
        `;

        keywords.forEach((keyword, index) => {
            // 修复有效性判断逻辑
            const validation = keyword.validation || {};
            const isValid = this.validationEnabled ? validation.is_valid : true;
            const validationClass = this.validationEnabled ? (isValid ? 'valid' : 'invalid') : '';
            const validationIcon = this.validationEnabled ? (isValid ? '<i class="fas fa-check-circle text-success"></i>' : '<i class="fas fa-times-circle text-danger"></i>') : '';
            
            html += `
                <div class="keyword-item ${validationClass}">
                    <div class="keyword-header">
                        <span class="keyword-name"><i class="fas fa-tag me-1"></i>${keyword.name}</span>
                        <span class="keyword-type"><i class="fas fa-cube me-1"></i>${keyword.type}</span>
                        <span class="keyword-confidence"><i class="fas fa-chart-line me-1"></i>${(keyword.confidence || 0).toFixed(2)}</span>
                        ${validationIcon ? `<span class="validation-icon">${validationIcon}</span>` : ''}
                    </div>
                    ${keyword.description ? `<div class="keyword-description"><i class="fas fa-info-circle me-1"></i>${keyword.description}</div>` : ''}
                    ${this.validationEnabled && validation.reason ? `
                        <div class="validation-details">
                            <small><i class="fas fa-shield-alt me-1"></i><strong>验证:</strong> ${validation.reason}</small>
                            ${validation.suggestions && validation.suggestions.length > 0 ? `
                                <div class="validation-suggestions">
                                    <small><i class="fas fa-lightbulb me-1"></i><strong>建议:</strong> ${validation.suggestions.join('; ')}</small>
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    buildRelationshipsHTML(result) {
        const relationships = result.relationships;
        const validRelationships = result.valid_relationships || [];
        
        let html = `
            <div class="relationships-section">
                <h4><i class="fas fa-project-diagram me-2"></i>提取的关系 (${relationships.length})</h4>
                <div class="relationships-list">
        `;

        relationships.forEach((rel, index) => {
            // 修复有效性判断逻辑
            const validation = rel.validation || {};
            const isValid = this.validationEnabled ? validation.is_valid : true;
            const validationClass = this.validationEnabled ? (isValid ? 'valid' : 'invalid') : '';
            const validationIcon = this.validationEnabled ? (isValid ? '<i class="fas fa-check-circle text-success"></i>' : '<i class="fas fa-times-circle text-danger"></i>') : '';
            
            const sourceName = rel.source?.name || 'Unknown';
            const targetName = rel.target?.name || 'Unknown';
            const relType = rel.type || 'Unknown';
            
            html += `
                <div class="relationship-item ${validationClass}">
                    <div class="relationship-header">
                        <span class="relationship-source"><i class="fas fa-circle me-1"></i>${sourceName}</span>
                        <span class="relationship-type"><i class="fas fa-arrow-right me-1"></i>${relType}</span>
                        <span class="relationship-target"><i class="fas fa-circle me-1"></i>${targetName}</span>
                        <span class="relationship-confidence"><i class="fas fa-chart-line me-1"></i>${(rel.confidence || 0).toFixed(2)}</span>
                        ${validationIcon ? `<span class="validation-icon">${validationIcon}</span>` : ''}
                    </div>
                    ${rel.description ? `<div class="relationship-description"><i class="fas fa-info-circle me-1"></i>${rel.description}</div>` : ''}
                    ${this.validationEnabled && validation.reason ? `
                        <div class="validation-details">
                            <small><i class="fas fa-shield-alt me-1"></i><strong>验证:</strong> ${validation.reason}</small>
                            ${validation.suggestions && validation.suggestions.length > 0 ? `
                                <div class="validation-suggestions">
                                    <small><i class="fas fa-lightbulb me-1"></i><strong>建议:</strong> ${validation.suggestions.join('; ')}</small>
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    async submitFeedback(type, correction = '') {
        try {
            // 获取最新的提取结果
            const resultsContainer = document.getElementById('extraction-results');
            const keywordItems = resultsContainer.querySelectorAll('.keyword-item');
            const relationshipItems = resultsContainer.querySelectorAll('.relationship-item');
            
            // 构建反馈数据
            const feedbackData = {
                type: type,
                correction: correction,
                keywords: [],
                relationships: []
            };

            // 收集关键词反馈
            keywordItems.forEach(item => {
                const name = item.querySelector('.keyword-name')?.textContent;
                if (name) {
                    feedbackData.keywords.push({
                        name: name,
                        is_valid: item.classList.contains('valid')
                    });
                }
            });

            // 收集关系反馈
            relationshipItems.forEach(item => {
                const source = item.querySelector('.relationship-source')?.textContent;
                const type = item.querySelector('.relationship-type')?.textContent;
                const target = item.querySelector('.relationship-target')?.textContent;
                
                if (source && type && target) {
                    feedbackData.relationships.push({
                        source: source,
                        type: type,
                        target: target,
                        is_valid: item.classList.contains('valid')
                    });
                }
            });

            const response = await fetch('/api/submit_feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('反馈提交成功，感谢您的帮助！');
                if (result.feedback_summary) {
                    console.log('反馈摘要:', result.feedback_summary);
                }
            } else {
                this.showError('反馈提交失败: ' + result.message);
            }
        } catch (error) {
            console.error('反馈提交失败:', error);
            this.showError('反馈提交失败，请稍后重试');
        }
    }

    async loadValidationStats() {
        if (!this.validationEnabled) return;

        try {
            const response = await fetch('/api/validation_stats');
            const stats = await response.json();
            
            if (stats && !stats.error) {
                document.getElementById('validity-rate').textContent = 
                    stats.validity_rate ? `${(stats.validity_rate * 100).toFixed(1)}%` : '-';
                document.getElementById('total-validations').textContent = 
                    stats.total_validations || '-';
                document.getElementById('avg-confidence').textContent = 
                    stats.average_confidence ? stats.average_confidence.toFixed(2) : '-';
            }
        } catch (error) {
            console.error('加载验证统计失败:', error);
        }
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            document.getElementById('content-input').value = content;
        };
        reader.readAsText(file);
    }

    showLoading(show) {
        const extractBtn = document.getElementById('extract-btn');
        const loadingElement = document.getElementById('extraction-loading');
        const resultsCard = document.getElementById('results-card');
        
        if (show) {
            // 更新按钮状态
            extractBtn.disabled = true;
            extractBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>提取中...';
            
            // 显示加载动画
            if (loadingElement) loadingElement.style.display = 'block';
            
            // 隐藏结果卡片
            if (resultsCard) resultsCard.classList.remove('show');
        } else {
            // 恢复按钮状态
            extractBtn.disabled = false;
            extractBtn.innerHTML = '<i class="fas fa-magic me-2"></i> 提取知识点';
            
            // 隐藏加载动画
            if (loadingElement) loadingElement.style.display = 'none';
        }
    }

    showError(message) {
        // 使用与问答系统一致的消息提示
        if (typeof showMessage !== 'undefined') {
            showMessage(message, 'danger');
        } else {
            alert('错误: ' + message);
        }
    }

    showSuccess(message) {
        // 使用与问答系统一致的消息提示
        if (typeof showMessage !== 'undefined') {
            showMessage(message, 'success');
        } else {
            alert('成功: ' + message);
        }
    }
}

// 初始化增强版知识点提取模块
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedKnowledgeExtraction = new EnhancedKnowledgeExtraction();
});