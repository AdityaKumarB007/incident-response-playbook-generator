const API_BASE_URL = 'http://127.0.0.1:5001/api';

// State to store chart instances for updates
let attackTypeChartInstance = null;
let severityChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Attempt to initialize database with dummy events if not already done
    try {
        await fetch(`${API_BASE_URL}/init`, { method: 'POST' });
    } catch (e) {
        console.error("Init call failed, continuing anyway...", e);
    }
    loadDashboardData();
    
    // Poll for live attacks
    setInterval(loadDashboardData, 3000);
});

function showSection(sectionId, element) {
    document.querySelectorAll('.content-section').forEach(sec => sec.style.display = 'none');
    document.getElementById(sectionId).style.display = 'block';
    
    document.querySelectorAll('.nav li').forEach(li => li.classList.remove('active'));
    element.classList.add('active');
}

async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/incidents`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const data = result.data;
            updateStats(data);
            renderCharts(data);
            renderTables(data);
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

function getBadgeClass(severity) {
    severity = (severity || "").toUpperCase();
    if (severity === 'CRITICAL') return 'badge-critical';
    if (severity === 'HIGH') return 'badge-high';
    if (severity === 'MEDIUM') return 'badge-medium';
    return 'badge-low';
}

function updateStats(data) {
    document.getElementById('total-attacks').innerText = data.length;
    
    const criticals = data.filter(d => d.severity === 'CRITICAL' || d.severity === 'HIGH').length;
    document.getElementById('critical-attacks').innerText = criticals;
    
    const endpoints = new Set(data.map(d => d.endpoint)).size;
    document.getElementById('unique-endpoints').innerText = endpoints;
    
    const ips = new Set(data.map(d => d.source_ip)).size;
    document.getElementById('unique-ips').innerText = ips;
}

function renderCharts(data) {
    // Aggregate by Attack Type
    const attackCounts = {};
    data.forEach(d => {
        attackCounts[d.attack_type] = (attackCounts[d.attack_type] || 0) + 1;
    });

    const ctxType = document.getElementById('attackTypeChart').getContext('2d');
    if (attackTypeChartInstance) attackTypeChartInstance.destroy();
    
    attackTypeChartInstance = new Chart(ctxType, {
        type: 'doughnut',
        data: {
            labels: Object.keys(attackCounts),
            datasets: [{
                data: Object.values(attackCounts),
                backgroundColor: ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'right', labels: { color: '#f8fafc' } } }
        }
    });

    // Aggregate by Severity
    const severityCounts = { 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0 };
    data.forEach(d => {
        if (severityCounts[d.severity] !== undefined) {
            severityCounts[d.severity]++;
        }
    });

    const ctxSeverity = document.getElementById('severityChart').getContext('2d');
    if (severityChartInstance) severityChartInstance.destroy();
    
    severityChartInstance = new Chart(ctxSeverity, {
        type: 'bar',
        data: {
            labels: Object.keys(severityCounts),
            datasets: [{
                label: 'Incident Count',
                data: Object.values(severityCounts),
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#7f1d1d'],
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderTables(data) {
    const recentBody = document.getElementById('incidents-table-body');
    const fullBody = document.getElementById('full-incidents-body');
    
    recentBody.innerHTML = '';
    fullBody.innerHTML = '';

    // Show latest 5 in Dashboard
    data.slice(0, 5).forEach(incident => {
        recentBody.innerHTML += buildRow(incident);
    });

    // Show all in Incidents tab
    data.forEach(incident => {
        fullBody.innerHTML += buildFullRow(incident);
    });
}

function buildRow(incident) {
    return `
        <tr>
            <td>${new Date(incident.timestamp).toLocaleString()}</td>
            <td><strong>${incident.attack_type}</strong></td>
            <td><code>${incident.source_ip}</code></td>
            <td><span class="badge ${getBadgeClass(incident.severity)}">${incident.severity}</span></td>
            <td>
                <button class="btn btn-primary" onclick="viewPlaybook('${incident.incident_id}')">
                    <i class="fa-solid fa-bolt"></i> Playbook
                </button>
            </td>
        </tr>
    `;
}

function buildFullRow(incident) {
    return `
        <tr>
            <td style="font-size: 11px; color:#94a3b8;">${incident.incident_id.split('-')[0]}...</td>
            <td>${new Date(incident.timestamp).toLocaleString()}</td>
            <td><strong>${incident.attack_type}</strong></td>
            <td><code>${incident.source_ip}</code></td>
            <td>${incident.endpoint}</td>
            <td><span class="badge ${getBadgeClass(incident.severity)}">${incident.severity}</span></td>
            <td>
                <button class="btn btn-primary" onclick="viewPlaybook('${incident.incident_id}')">
                    <i class="fa-solid fa-list-check"></i> Respond
                </button>
            </td>
        </tr>
    `;
}

// Playbook Functions
async function viewPlaybook(incidentId) {
    const modal = document.getElementById('playbook-modal');
    
    try {
        const response = await fetch(`${API_BASE_URL}/playbook/${incidentId}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const data = result.data;
            const inc = result.incident;
            
            document.getElementById('pb-id').innerText = data.incident_id;
            document.getElementById('pb-type').innerText = data.attack_type;
            
            document.getElementById('pb-ip').innerText = inc.source_ip;
            document.getElementById('pb-severity').innerText = inc.severity;
            document.getElementById('pb-severity').className = `badge ${getBadgeClass(inc.severity)}`;
            document.getElementById('pb-evidence').innerText = inc.evidence;
            
            const stepsHtml = data.playbook_steps.map((step, idx) => `
                <div class="checklist-item">
                    <input type="checkbox" id="step-${idx}">
                    <label for="step-${idx}">${step}</label>
                </div>
            `).join('');
            
            document.getElementById('pb-steps').innerHTML = stepsHtml;
            modal.style.display = 'block';
        } else {
            alert('Failed to load playbook.');
        }
    } catch (e) {
        console.error(e);
        alert('Error communicating with backend.');
    }
}

function closeModal() {
    document.getElementById('playbook-modal').style.display = 'none';
}

function exportPlaybookPDF() {
    const element = document.getElementById('printable-playbook');
    const modalContent = document.getElementById('playbook-content-wrapper');
    
    // Apply styling so it prints clearly on PDF
    element.classList.add('pdf-mode');
    
    // Temporarily disabled scroll clipping for html2canvas
    const origMaxHeight = modalContent.style.maxHeight;
    const origOverflow = modalContent.style.overflow;
    modalContent.style.maxHeight = 'none';
    modalContent.style.overflow = 'visible';
    
    const opt = {
        margin:       10,
        filename:     `IR-Playbook-${document.getElementById('pb-id').innerText}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { 
            scale: 2, 
            useCORS: true, 
            backgroundColor: '#ffffff',
            windowY: 0,
            scrollY: 0
        },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        // Clean up the style after rendering
        element.classList.remove('pdf-mode');
        modalContent.style.maxHeight = origMaxHeight;
        modalContent.style.overflow = origOverflow;
    });
}

