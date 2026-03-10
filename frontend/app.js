const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

let ws = null;
let workflows = new Map();
let nodePositions = new Map();
let activeFlows = new Map();
let draggingNode = null;
let dragOffset = { x: 0, y: 0 };
let animationId = null;

const NODE_RADIUS = 25;
const PARTICLE_RADIUS = 6;
const COLORS = {
    node: '#4ecca3',
    nodeLabel: '#fff',
    edge: '#333',
    edgeActive: '#e94560',
    particle: '#e94560',
    particleGlow: 'rgba(233, 69, 96, 0.3)',
};

function resizeCanvas() {
    const container = canvas.parentElement;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onopen = () => {
        document.getElementById('status').textContent = 'Connected';
        document.getElementById('status').classList.add('connected');
    };
    
    ws.onclose = () => {
        document.getElementById('status').textContent = 'Disconnected';
        document.getElementById('status').classList.remove('connected');
        setTimeout(connectWebSocket, 2000);
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };
}

function handleMessage(message) {
    switch (message.type) {
        case 'init':
            workflows.clear();
            message.workflows.forEach(w => workflows.set(w.id, w));
            initNodePositions();
            applyForceDirectedLayout();
            updateUI();
            break;
        case 'workflow_added':
            workflows.set(message.workflow.id, message.workflow);
            initNodePositions();
            applyForceDirectedLayout();
            updateUI();
            break;
        case 'workflow_updated':
            workflows.set(message.workflow.id, message.workflow);
            updateUI();
            break;
        case 'workflow_deleted':
            workflows.delete(message.id);
            updateUI();
            break;
        case 'flow_added':
            const wf = workflows.get(message.workflow_id);
            if (wf) {
                wf.flows.push(message.flow);
                activeFlows.set(`${message.workflow_id}:${message.flow.id}`, {
                    ...message.flow,
                    workflowId: message.workflow_id,
                    startTime: Date.now(),
                });
            }
            break;
        case 'flow_removed':
            activeFlows.delete(`${message.workflow_id}:${message.flow_id}`);
            const workflow = workflows.get(message.workflow_id);
            if (workflow) {
                workflow.flows = workflow.flows.filter(f => f.id !== message.flow_id);
            }
            break;
    }
}

function updateUI() {
    const select = document.getElementById('workflowSelect');
    select.innerHTML = '<option value="">Select workflow...</option>';
    
    const list = document.getElementById('workflowList');
    list.innerHTML = '';
    
    workflows.forEach((wf, id) => {
        const option = document.createElement('option');
        option.value = id;
        option.textContent = id;
        select.appendChild(option);
        
        const item = document.createElement('div');
        item.className = 'workflow-item';
        item.innerHTML = `
            <span>${id} (${wf.nodes.length} nodes)</span>
            <button class="delete-btn" data-id="${id}">Delete</button>
        `;
        list.appendChild(item);
    });
    
    list.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            await fetch(`/workflows/${id}`, { method: 'DELETE' });
        });
    });
}

function initNodePositions() {
    workflows.forEach((wf) => {
        const key = `wf_${wf.id}`;
        if (!nodePositions.has(key)) {
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(canvas.width, canvas.height) * 0.3;
            
            wf.nodes.forEach((node, i) => {
                const angle = (2 * Math.PI * i) / wf.nodes.length;
                nodePositions.set(`${key}_${node.id}`, {
                    x: centerX + radius * Math.cos(angle),
                    y: centerY + radius * Math.sin(angle),
                    vx: 0,
                    vy: 0,
                });
            });
        }
    });
}

function applyForceDirectedLayout() {
    const iterations = 3;
    const repulsion = 5000;
    const attraction = 0.01;
    const damping = 0.9;
    
    for (let iter = 0; iter < iterations; iter++) {
        workflows.forEach((wf) => {
            const key = `wf_${wf.id}`;
            
            wf.nodes.forEach((node1, i) => {
                const pos1 = nodePositions.get(`${key}_${node1.id}`);
                if (!pos1) return;
                
                wf.nodes.forEach((node2, j) => {
                    if (i >= j) return;
                    const pos2 = nodePositions.get(`${key}_${node2.id}`);
                    if (!pos2) return;
                    
                    const dx = pos2.x - pos1.x;
                    const dy = pos2.y - pos1.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                    const force = repulsion / (dist * dist);
                    
                    pos1.vx -= (dx / dist) * force;
                    pos1.vy -= (dy / dist) * force;
                    pos2.vx += (dx / dist) * force;
                    pos2.vy += (dy / dist) * force;
                });
            });
            
            wf.edges.forEach((edge) => {
                const posFrom = nodePositions.get(`${key}_${edge.from_node}`);
                const posTo = nodePositions.get(`${key}_${edge.to_node}`);
                if (!posFrom || !posTo) return;
                
                const dx = posTo.x - posFrom.x;
                const dy = posTo.y - posFrom.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = (dist - 100) * attraction;
                
                posFrom.vx += (dx / dist) * force;
                posFrom.vy += (dy / dist) * force;
                posTo.vx -= (dx / dist) * force;
                posTo.vy -= (dy / dist) * force;
            });
            
            wf.nodes.forEach((node) => {
                const pos = nodePositions.get(`${key}_${node.id}`);
                if (!pos) return;
                
                const dx = canvas.width / 2 - pos.x;
                const dy = canvas.height / 2 - pos.y;
                pos.vx += dx * 0.001;
                pos.vy += dy * 0.001;
            });
            
            wf.nodes.forEach((node) => {
                const pos = nodePositions.get(`${key}_${node.id}`);
                if (!pos) return;
                
                pos.x += pos.vx;
                pos.y += pos.vy;
                pos.vx *= damping;
                pos.vy *= damping;
                
                pos.x = Math.max(NODE_RADIUS, Math.min(canvas.width - NODE_RADIUS, pos.x));
                pos.y = Math.max(NODE_RADIUS, Math.min(canvas.height - NODE_RADIUS, pos.y));
            });
        });
    }
}

function getEdgeKey(from, to) {
    return from < to ? `${from}->${to}` : `${to}->${from}`;
}

function render() {
    ctx.fillStyle = '#0f0f1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    const edgeDrawn = new Set();
    
    workflows.forEach((wf) => {
        const key = `wf_${wf.id}`;
        
        wf.edges.forEach((edge) => {
            const fromPos = nodePositions.get(`${key}_${edge.from_node}`);
            const toPos = nodePositions.get(`${key}_${edge.to_node}`);
            if (!fromPos || !toPos) return;
            
            ctx.strokeStyle = COLORS.edge;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(fromPos.x, fromPos.y);
            ctx.lineTo(toPos.x, toPos.y);
            ctx.stroke();
        });
        
        activeFlows.forEach((flow, flowKey) => {
            if (!flow.path || flow.path.length < 2) return;
            
            const flowKey2 = `wf_${flow.workflowId}`;
            
            const elapsed = Date.now() - flow.startTime;
            const duration = flow.duration_ms;
            const progress = (elapsed % duration) / duration;
            
            for (let i = 0; i < flow.path.length - 1; i++) {
                const fromNode = flow.path[i];
                const toNode = flow.path[i + 1];
                
                const fromPos = nodePositions.get(`${flowKey2}_${fromNode}`);
                const toPos = nodePositions.get(`${flowKey2}_${toNode}`);
                if (!fromPos || !toPos) continue;
                
                const segmentProgress = progress * flow.path.length - i;
                if (segmentProgress < 0 || segmentProgress > 1) continue;
                
                const x = fromPos.x + (toPos.x - fromPos.x) * segmentProgress;
                const y = fromPos.y + (toPos.y - fromPos.y) * segmentProgress;
                
                ctx.fillStyle = COLORS.particleGlow;
                ctx.beginPath();
                ctx.arc(x, y, PARTICLE_RADIUS * 2, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.fillStyle = COLORS.particle;
                ctx.beginPath();
                ctx.arc(x, y, PARTICLE_RADIUS, 0, Math.PI * 2);
                ctx.fill();
            }
        });
        
        wf.nodes.forEach((node) => {
            const pos = nodePositions.get(`${key}_${node.id}`);
            if (!pos) return;
            
            ctx.fillStyle = COLORS.node;
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, NODE_RADIUS, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.fillStyle = COLORS.nodeLabel;
            ctx.font = '12px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(node.label || node.id, pos.x, pos.y);
        });
    });
    
    animationId = requestAnimationFrame(render);
}

function getNodeAtPosition(x, y) {
    for (const [posKey, pos] of nodePositions) {
        const dx = x - pos.x;
        const dy = y - pos.y;
        if (Math.sqrt(dx * dx + dy * dy) <= NODE_RADIUS) {
            return posKey;
        }
    }
    return null;
}

canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const nodeKey = getNodeAtPosition(x, y);
    if (nodeKey) {
        const pos = nodePositions.get(nodeKey);
        draggingNode = nodeKey;
        dragOffset.x = x - pos.x;
        dragOffset.y = y - pos.y;
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (!draggingNode) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const pos = nodePositions.get(draggingNode);
    if (pos) {
        pos.x = x - dragOffset.x;
        pos.y = y - dragOffset.y;
    }
});

canvas.addEventListener('mouseup', () => {
    draggingNode = null;
});

canvas.addEventListener('mouseleave', () => {
    draggingNode = null;
});

document.getElementById('addWorkflowBtn').addEventListener('click', async () => {
    const id = `workflow_${Date.now()}`;
    const nodes = [
        { id: 'n1', label: 'Start' },
        { id: 'n2', label: 'Process' },
        { id: 'n3', label: 'Decision' },
        { id: 'n4', label: 'Action A' },
        { id: 'n5', label: 'Action B' },
        { id: 'n6', label: 'End' },
    ];
    const edges = [
        { from_node: 'n1', to_node: 'n2' },
        { from_node: 'n2', to_node: 'n3' },
        { from_node: 'n3', to_node: 'n4' },
        { from_node: 'n3', to_node: 'n5' },
        { from_node: 'n4', to_node: 'n6' },
        { from_node: 'n5', to_node: 'n6' },
    ];
    
    await fetch('/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, nodes, edges, flows: [] }),
    });
});

document.getElementById('addFlowBtn').addEventListener('click', () => {
    const workflowId = document.getElementById('workflowSelect').value;
    const pathStr = document.getElementById('flowPath').value;
    const duration = parseInt(document.getElementById('flowDuration').value) || 5000;
    
    if (!workflowId || !pathStr) return;
    
    const path = pathStr.split(',').map(s => s.trim());
    if (path.length < 2) return;
    
    ws.send(JSON.stringify({
        type: 'add_flow',
        workflow_id: workflowId,
        flow: {
            id: `flow_${Date.now()}`,
            path,
            duration_ms: duration,
        },
    }));
});

window.addEventListener('resize', () => {
    resizeCanvas();
    nodePositions.clear();
    initNodePositions();
});

resizeCanvas();
initNodePositions();
applyForceDirectedLayout();
connectWebSocket();
render();
