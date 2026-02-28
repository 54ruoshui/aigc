/**
 * Neo4j图谱性能优化和用户体验增强模块
 */

class GraphPerformanceOptimizer {
    constructor(graphInstance) {
        this.graph = graphInstance;
        this.performanceMode = false;
        this.animationFrame = null;
        this.resizeObserver = null;
        this.intersectionObserver = null;
        this.visibilityObserver = null;
        
        this.init();
    }
    
    init() {
        this.setupResizeObserver();
        this.setupVisibilityObserver();
        this.setupIntersectionObserver();
        this.setupKeyboardShortcuts();
        this.setupPerformanceMonitoring();
    }
    
    setupIntersectionObserver() {
        if (typeof IntersectionObserver !== 'undefined') {
            this.intersectionObserver = new IntersectionObserver(
                entries => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.resumeAnimation();
                        } else {
                            this.pauseAnimation();
                        }
                    });
                },
                { threshold: 0.1 }
            );
            
            this.intersectionObserver.observe(this.graph.container.node());
        }
    }
    
    // 响应式调整
    setupResizeObserver() {
        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver(entries => {
                for (let entry of entries) {
                    const { width, height } = entry.contentRect;
                    this.graph.resize(width, height);
                }
            });
            
            this.resizeObserver.observe(this.graph.container.node());
        }
    }
    
    // 可见性检测
    setupVisibilityObserver() {
        if (typeof IntersectionObserver !== 'undefined') {
            this.intersectionObserver = new IntersectionObserver(
                entries => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.resumeAnimation();
                        } else {
                            this.pauseAnimation();
                        }
                    });
                },
                { threshold: 0.1 }
            );
            
            this.intersectionObserver.observe(this.graph.container.node());
        }
    }
    
    // 页面可见性检测
    setupVisibilityObserver() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimation();
            } else {
                this.resumeAnimation();
            }
        });
    }
    
    // 键盘快捷键
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch (event.key) {
                case 'r':
                case 'R':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.graph.resetZoom();
                    }
                    break;
                case 'f':
                case 'F':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.graph.zoomToFit();
                    }
                    break;
                case 'e':
                case 'E':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.graph.exportAsSVG();
                    }
                    break;
                case 'p':
                case 'P':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.togglePerformanceMode();
                    }
                    break;
            }
        });
    }
    
    // 性能监控
    setupPerformanceMonitoring() {
        if ('performance' in window && 'memory' in performance) {
            setInterval(() => {
                const memoryUsage = performance.memory.usedJSHeapSize / 1048576;
                if (memoryUsage > 100) { // 超过100MB时启用性能模式
                    this.enablePerformanceMode();
                }
            }, 5000);
        }
    }
    
    // 暂停动画
    pauseAnimation() {
        if (this.graph.simulation) {
            this.graph.simulation.stop();
        }
    }
    
    // 恢复动画
    resumeAnimation() {
        if (this.graph.simulation && !this.performanceMode) {
            this.graph.simulation.alpha(0.3).restart();
        }
    }
    
    // 切换性能模式
    togglePerformanceMode() {
        if (this.performanceMode) {
            this.disablePerformanceMode();
        } else {
            this.enablePerformanceMode();
        }
    }
    
    // 启用性能模式
    enablePerformanceMode() {
        this.performanceMode = true;
        
        // 降低动画质量
        if (this.graph.simulation) {
            this.graph.simulation.alphaDecay(0.1);
            this.graph.simulation.velocityDecay(0.5);
        }
        
        // 简化视觉效果
        this.graph.container.selectAll('.node circle')
            .transition()
            .duration(200)
            .attr('filter', null);
        
        // 降低更新频率
        this.throttleUpdates();
        
        console.log('性能模式已启用');
    }
    
    // 禁用性能模式
    disablePerformanceMode() {
        this.performanceMode = false;
        
        // 恢复动画质量
        if (this.graph.simulation) {
            this.graph.simulation.alphaDecay(0.0228);
            this.graph.simulation.velocityDecay(0.4);
        }
        
        // 恢复视觉效果
        this.graph.container.selectAll('.node circle')
            .transition()
            .duration(200)
            .attr('filter', 'url(#drop-shadow)');
        
        // 恢复更新频率
        this.unthrottleUpdates();
        
        console.log('性能模式已禁用');
    }
    
    // 节流更新
    throttleUpdates() {
        if (this.graph.simulation) {
            const originalTick = this.graph.simulation.on('tick');
            let lastUpdate = 0;
            
            this.graph.simulation.on('tick', () => {
                const now = Date.now();
                if (now - lastUpdate > 50) { // 限制更新频率为20fps
                    originalTick();
                    lastUpdate = now;
                }
            });
        }
    }
    
    // 取消节流
    unthrottleUpdates() {
        // 重新初始化模拟以恢复正常的更新频率
        if (this.graph.simulation) {
            this.graph.simulation.alpha(0.3).restart();
        }
    }
    
    // 内存清理
    cleanup() {
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
}

// 图谱交互增强
class GraphInteractionEnhancer {
    constructor(graphInstance) {
        this.graph = graphInstance;
        this.selectedNodes = new Set();
        this.highlightedPaths = [];
        this.minimap = null;
        
        this.init();
    }
    
    init() {
        this.setupMultiSelection();
        this.setupPathHighlighting();
        this.setupMinimap();
        this.setupSearch();
        this.setupTooltips();
    }
    
    // 多选功能
    setupMultiSelection() {
        this.graph.container.on('click', (event) => {
            if (event.defaultPrevented) return;
            
            // 点击空白处清除选择
            if (event.target === this.graph.svg.node()) {
                this.clearSelection();
            }
        });
    }
    
    // 路径高亮
    setupPathHighlighting() {
        // 为节点添加点击事件
        this.graph.container.selectAll('.node')
            .on('click', (event, d) => {
                if (event.ctrlKey || event.metaKey) {
                    this.toggleNodeSelection(d);
                } else {
                    this.clearSelection();
                    this.selectNode(d);
                }
            });
    }
    
    // 小地图
    setupMinimap() {
        const minimapContainer = this.graph.container.append('div')
            .attr('class', 'minimap')
            .style('position', 'absolute')
            .style('bottom', '10px')
            .style('right', '10px')
            .style('width', '150px')
            .style('height', '150px')
            .style('border', '1px solid #ccc')
            .style('background', 'rgba(255,255,255,0.9)')
            .style('border-radius', '5px')
            .style('overflow', 'hidden');
        
        // 这里可以添加小地图的实现
    }
    
    // 搜索功能
    setupSearch() {
        // 创建搜索框
        const searchBox = this.graph.container.append('div')
            .attr('class', 'graph-search')
            .style('position', 'absolute')
            .style('top', '10px')
            .style('left', '10px')
            .style('z-index', '1000');
        
        searchBox.append('input')
            .attr('type', 'text')
            .attr('placeholder', '搜索节点...')
            .style('padding', '5px 10px')
            .style('border', '1px solid #ccc')
            .style('border-radius', '3px')
            .style('width', '200px')
            .on('input', (event) => {
                this.searchNodes(event.target.value);
            });
    }
    
    // 增强工具提示
    setupTooltips() {
        // 使用更现代的工具提示库或自定义实现
    }
    
    // 搜索节点
    searchNodes(query) {
        if (!query) {
            this.clearSearch();
            return;
        }
        
        const lowerQuery = query.toLowerCase();
        
        this.graph.container.selectAll('.node')
            .style('opacity', d => {
                return d.name.toLowerCase().includes(lowerQuery) ? 1 : 0.3;
            });
        
        this.graph.container.selectAll('.link')
            .style('opacity', d => {
                const sourceMatch = d.source.name.toLowerCase().includes(lowerQuery);
                const targetMatch = d.target.name.toLowerCase().includes(lowerQuery);
                return sourceMatch || targetMatch ? 0.6 : 0.1;
            });
    }
    
    // 清除搜索
    clearSearch() {
        this.graph.container.selectAll('.node').style('opacity', 1);
        this.graph.container.selectAll('.link').style('opacity', 0.6);
    }
    
    // 选择节点
    selectNode(node) {
        this.selectedNodes.clear();
        this.selectedNodes.add(node);
        this.updateSelection();
    }
    
    // 切换节点选择
    toggleNodeSelection(node) {
        if (this.selectedNodes.has(node)) {
            this.selectedNodes.delete(node);
        } else {
            this.selectedNodes.add(node);
        }
        this.updateSelection();
    }
    
    // 清除选择
    clearSelection() {
        this.selectedNodes.clear();
        this.updateSelection();
    }
    
    // 更新选择显示
    updateSelection() {
        this.graph.container.selectAll('.node circle')
            .style('stroke', d => {
                return this.selectedNodes.has(d) ? '#ff6b6b' : '#fff';
            })
            .style('stroke-width', d => {
                return this.selectedNodes.has(d) ? 4 : 2;
            });
    }
}

// 导出类
window.GraphPerformanceOptimizer = GraphPerformanceOptimizer;
window.GraphInteractionEnhancer = GraphInteractionEnhancer;