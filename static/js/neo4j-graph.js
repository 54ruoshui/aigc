/**
 * Neo4j风格的知识图谱可视化组件
 * 提供专业的图谱渲染、交互和动画效果
 */

class Neo4jGraph {
    constructor(containerId, options = {}) {
        this.container = d3.select(`#${containerId}`);
        this.width = options.width || this.container.node().clientWidth;
        this.height = options.height || this.container.node().clientHeight;
        
        // 配置选项
        this.options = {
            nodeRadius: 25,
            linkDistance: 80,
            linkStrength: 0.5,
            chargeStrength: -300,
            gravityStrength: 0.1,
            fontSize: 12,
            strokeWidth: 2,
            ...options
        };
        
        // 颜色方案 - Neo4j风格
        this.colorScheme = {
            'Protocol': '#4A90E2',
            'Device': '#7B68EE',
            'Layer': '#48D1CC',
            'Knowledge': '#3CB371',
            'SecurityConcept': '#FFB347',
            'NetworkType': '#FF69B4',
            'Model': '#87CEEB',
            'Function': '#DDA0DD',
            'Topology': '#98FB98',
            'Problem': '#FF6B6B',
            'Solution': '#4ECDC4',
            'default': '#95A5A6'
        };
        
        // 状态变量
        this.simulation = null;
        this.svg = null;
        this.g = null;
        this.nodes = [];
        this.links = [];
        this.currentTransform = d3.zoomIdentity;
        
        this.init();
    }
    
    init() {
        // 清空容器
        this.container.selectAll('*').remove();
        
        // 创建SVG
        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', [0, 0, this.width, this.height])
            .style('background', 'radial-gradient(circle at center, #f8f9fa 0%, #e9ecef 100%)');
        
        // 定义渐变和滤镜
        this.defineGradientsAndFilters();
        
        // 创建主容器组
        this.g = this.svg.append('g');
        
        // 设置缩放行为
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.currentTransform = event.transform;
                this.g.attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
        
        // 创建力导向模拟
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(this.options.linkDistance))
            .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(this.options.nodeRadius * 1.5))
            .force('gravity', d3.forceManyBody().strength(this.options.gravityStrength));
    }
    
    defineGradientsAndFilters() {
        const defs = this.svg.append('defs');
        
        // 定义节点渐变
        Object.entries(this.colorScheme).forEach(([type, color]) => {
            const gradient = defs.append('radialGradient')
                .attr('id', `gradient-${type}`)
                .attr('cx', '30%')
                .attr('cy', '30%');
            
            gradient.append('stop')
                .attr('offset', '0%')
                .attr('stop-color', this.lightenColor(color, 20))
                .attr('stop-opacity', 0.9);
            
            gradient.append('stop')
                .attr('offset', '100%')
                .attr('stop-color', color)
                .attr('stop-opacity', 1);
        });
        
        // 定义阴影滤镜
        const filter = defs.append('filter')
            .attr('id', 'drop-shadow')
            .attr('height', '130%');
        
        filter.append('feGaussianBlur')
            .attr('in', 'SourceAlpha')
            .attr('stdDeviation', 3);
        
        filter.append('feOffset')
            .attr('dx', 2)
            .attr('dy', 2)
            .attr('result', 'offsetblur');
        
        filter.append('feComponentTransfer')
            .append('feFuncA')
            .attr('type', 'linear')
            .attr('slope', 0.3);
        
        filter.append('feMerge')
            .append('feMergeNode');
        
        filter.append('feMerge')
            .append('feMergeNode')
            .attr('in', 'SourceGraphic');
        
        // 定义箭头标记
        const marker = defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 8)
            .attr('markerHeight', 8)
            .attr('xoverflow', 'visible');
        
        marker.append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke', 'none');
    }
    
    lightenColor(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255))
            .toString(16).slice(1);
    }
    
    updateGraph(graphData) {
        if (!graphData || !graphData.nodes) {
            console.warn('图谱数据为空');
            return;
        }
        
        // 处理节点数据
        this.nodes = graphData.nodes.map((node, index) => ({
            id: node.name || `node-${index}`,
            name: node.name,
            type: node.type || 'default',
            description: node.description,
            ...node
        }));
        
        // 处理关系数据
        this.links = [];
        if (graphData.relationships) {
            graphData.relationships.forEach(rel => {
                if (rel.start && rel.end) {
                    this.links.push({
                        source: rel.start.name || rel.start,
                        target: rel.end.name || rel.end,
                        type: rel.type || 'RELATED_TO',
                        ...rel
                    });
                }
            });
        }
        
        this.render();
    }
    
    render() {
        // 清除现有元素
        this.g.selectAll('*').remove();
        
        // 创建关系线组
        const linkGroup = this.g.append('g').attr('class', 'links');
        
        // 创建关系线
        const links = linkGroup.selectAll('.link')
            .data(this.links)
            .enter().append('line')
            .attr('class', 'link')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrowhead)');
        
        // 创建关系标签
        const linkLabels = linkGroup.selectAll('.link-label')
            .data(this.links)
            .enter().append('text')
            .attr('class', 'link-label')
            .attr('text-anchor', 'middle')
            .attr('dy', -5)
            .attr('font-size', '10px')
            .attr('fill', '#666')
            .text(d => d.type);
        
        // 创建节点组
        const nodeGroup = this.g.append('g').attr('class', 'nodes');
        
        // 创建节点容器
        const nodes = nodeGroup.selectAll('.node')
            .data(this.nodes)
            .enter().append('g')
            .attr('class', 'node')
            .call(this.createDragBehavior());
        
        // 添加节点圆圈
        nodes.append('circle')
            .attr('r', this.options.nodeRadius)
            .attr('fill', d => `url(#gradient-${d.type})`)
            .attr('stroke', '#fff')
            .attr('stroke-width', this.options.strokeWidth)
            .attr('filter', 'url(#drop-shadow)')
            .on('click', (event, d) => this.showNodeDetails(event, d))
            .on('mouseover', (event, d) => this.highlightNode(d))
            .on('mouseout', () => this.unhighlightNodes());
        
        // 添加节点图标
        nodes.append('text')
            .attr('class', 'node-icon')
            .attr('text-anchor', 'middle')
            .attr('dy', '0.3em')
            .attr('font-size', '16px')
            .attr('fill', '#fff')
            .text(d => this.getNodeIcon(d.type));
        
        // 添加节点标签
        nodes.append('text')
            .attr('class', 'node-label')
            .attr('text-anchor', 'middle')
            .attr('dy', this.options.nodeRadius + 15)
            .attr('font-size', this.options.fontSize)
            .attr('fill', '#333')
            .attr('font-weight', '500')
            .text(d => this.truncateText(d.name, 12));
        
        // 更新力导向模拟
        this.simulation
            .nodes(this.nodes)
            .on('tick', () => this.ticked(links, linkLabels, nodes));
        
        this.simulation.force('link')
            .links(this.links);
        
        this.simulation.alpha(1).restart();
    }
    
    createDragBehavior() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    ticked(links, linkLabels, nodes) {
        links
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        linkLabels
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);
        
        nodes.attr('transform', d => `translate(${d.x},${d.y})`);
    }
    
    getNodeIcon(type) {
        const icons = {
            'Protocol': '⚡',
            'Device': '🖥️',
            'Layer': '📊',
            'Knowledge': '💡',
            'SecurityConcept': '🔒',
            'NetworkType': '🌐',
            'Model': '📋',
            'Function': '⚙️',
            'Topology': '🔗',
            'Problem': '⚠️',
            'Solution': '✅'
        };
        return icons[type] || '📍';
    }
    
    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    highlightNode(node) {
        // 高亮相关节点和关系
        d3.selectAll('.node circle')
            .style('opacity', d => d === node ? 1 : 0.3);
        
        d3.selectAll('.link')
            .style('opacity', d => d.source === node || d.target === node ? 0.8 : 0.1);
    }
    
    unhighlightNodes() {
        d3.selectAll('.node circle').style('opacity', 1);
        d3.selectAll('.link').style('opacity', 0.6);
    }
    
    showNodeDetails(event, node) {
        // 创建详细信息面板
        const details = this.createNodeDetails(node);
        
        // 显示在合适的位置
        const tooltip = d3.select('body').append('div')
            .attr('class', 'neo4j-tooltip')
            .style('position', 'absolute')
            .style('background', 'white')
            .style('border', '1px solid #ddd')
            .style('border-radius', '8px')
            .style('padding', '15px')
            .style('box-shadow', '0 4px 20px rgba(0,0,0,0.15)')
            .style('max-width', '350px')
            .style('z-index', '1000')
            .style('font-family', 'Arial, sans-serif')
            .html(details);
        
        // 设置位置
        const tooltipNode = tooltip.node();
        const tooltipRect = tooltipNode.getBoundingClientRect();
        const containerRect = this.container.node().getBoundingClientRect();
        
        let left = event.pageX + 10;
        let top = event.pageY - tooltipRect.height / 2;
        
        // 确保不超出视窗
        if (left + tooltipRect.width > window.innerWidth) {
            left = event.pageX - tooltipRect.width - 10;
        }
        if (top < 0) {
            top = 10;
        }
        if (top + tooltipRect.height > window.innerHeight) {
            top = window.innerHeight - tooltipRect.height - 10;
        }
        
        tooltip.style('left', left + 'px')
            .style('top', top + 'px');
        
        // 点击其他地方关闭
        const closeTooltip = () => {
            tooltip.remove();
            document.removeEventListener('click', closeTooltip);
        };
        
        setTimeout(() => {
            document.addEventListener('click', closeTooltip);
        }, 100);
    }
    
    createNodeDetails(node) {
        let details = `
            <div style="border-bottom: 2px solid ${this.colorScheme[node.type] || this.colorScheme.default}; margin-bottom: 10px; padding-bottom: 8px;">
                <h3 style="margin: 0; color: ${this.colorScheme[node.type] || this.colorScheme.default}; font-size: 16px;">
                    ${this.getNodeIcon(node.type)} ${node.name}
                </h3>
                <span style="background: ${this.colorScheme[node.type] || this.colorScheme.default}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">
                    ${node.type}
                </span>
            </div>
        `;
        
        if (node.description) {
            details += `<p style="margin: 8px 0; color: #666; font-size: 13px;">${node.description}</p>`;
        }
        
        // 添加其他属性
        Object.keys(node).forEach(key => {
            if (!['id', 'name', 'type', 'description', 'x', 'y', 'fx', 'fy', 'vx', 'vy', 'index'].includes(key) && node[key]) {
                const value = Array.isArray(node[key]) ? node[key].join(', ') : node[key];
                details += `
                    <div style="margin: 5px 0;">
                        <strong style="color: #333; font-size: 12px;">${key}:</strong>
                        <span style="color: #666; font-size: 12px;">${value}</span>
                    </div>
                `;
            }
        });
        
        // 添加统计信息
        const connectedNodes = this.links.filter(l => l.source.id === node.id || l.target.id === node.id).length;
        details += `
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; font-size: 11px; color: #888;">
                连接数: ${connectedNodes}
            </div>
        `;
        
        return details;
    }
    
    // 公共方法
    resize(width, height) {
        this.width = width;
        this.height = height;
        this.svg.attr('width', width).attr('height', height);
        this.simulation.force('center', d3.forceCenter(width / 2, height / 2));
        this.simulation.alpha(0.3).restart();
    }
    
    resetZoom() {
        this.svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity);
    }
    
    zoomToFit() {
        const bounds = this.g.node().getBBox();
        const fullWidth = this.width;
        const fullHeight = this.height;
        const width = bounds.width;
        const height = bounds.height;
        const midX = bounds.x + width / 2;
        const midY = bounds.y + height / 2;
        
        if (width == 0 || height == 0) return;
        
        const scale = 0.8 / Math.max(width / fullWidth, height / fullHeight);
        const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];
        
        this.svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
    }
    
    exportAsSVG() {
        const svgData = this.svg.node().outerHTML;
        const blob = new Blob([svgData], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `neo4j-graph-${Date.now()}.svg`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        this.container.selectAll('*').remove();
    }
}

// 导出类供其他模块使用
window.Neo4jGraph = Neo4jGraph;