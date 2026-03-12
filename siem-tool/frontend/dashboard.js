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
    
    // Also load MongoDB Historical Templates
    loadTemplates();
}

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE_URL}/templates`);
        const result = await response.json();
        
        if (result.status === 'success') {
            renderTemplates(result.data);
        }
    } catch (error) {
        console.error('Error fetching templates:', error);
    }
}

function renderTemplates(templates) {
    const container = document.getElementById('templates-container');
    if (!container) return;
    
    if (!templates || templates.length === 0) {
        container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px;">
            <i class="fa-solid fa-folder-open"></i> No historical templates found in MongoDB yet.
        </div>`;
        return;
    }
    
    let html = '';
    templates.forEach(t => {
        const tDate = new Date(t.created_at).toLocaleString();
        
        // Convert the story array into actual visually separated steps
        let stepsHtml = '';
        if (t.generated_playbook_story && t.generated_playbook_story.length > 0) {
            stepsHtml = t.generated_playbook_story.map(step => {
                // Formatting specific numbering and headers for better display
                let formattedStep = step.replace(/\n/g, '<br>');
                return `<div style="margin-top: 10px; padding: 12px; background: rgba(255,255,255,0.03); border-left: 3px solid var(--accent-blue); border-radius: 4px;">${formattedStep}</div>`;
            }).join('');
        }

        html += `
            <div class="card" style="border: 1px solid var(--border-color); margin-bottom: 0;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;">
                    <div>
                        <h4 style="color: var(--accent-blue); margin-bottom: 4px; font-size: 16px;">
                            <i class="fa-solid fa-file-shield"></i> ${t.attack_type}
                        </h4>
                        <p style="font-size: 12px; color: var(--text-secondary);">
                            <i class="fa-solid fa-crosshairs"></i> Targeted: <code>${t.target_endpoint}</code> | <i class="fa-solid fa-network-wired"></i> Source: <code>${t.source_ip}</code>
                        </p>
                    </div>
                    <span class="badge badge-medium" style="background: rgba(255,255,255,0.1); color: var(--text-secondary); border: none;">
                        <i class="fa-regular fa-clock"></i> ${tDate}
                    </span>
                </div>
                
                <div style="margin-top: 16px;">
                    <h5 style="color: var(--text-secondary); text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; margin-bottom: 8px;">Incident Response Story & Remediation</h5>
                    ${stepsHtml}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
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

    // Filter to only show HIGH and CRITICAL in the recent dashboard table
    const severeIncidents = data.filter(d => 
        (d.severity || '').toUpperCase() === 'HIGH' || 
        (d.severity || '').toUpperCase() === 'CRITICAL'
    );

    // Show latest 5 severe incidents in Dashboard
    severeIncidents.slice(0, 5).forEach(incident => {
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
                    <i class="fa-solid fa-shield-virus"></i> Action
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
                    <i class="fa-solid fa-list-check"></i> Prevent
                </button>
            </td>
        </tr>
    `;
}

// Playbook Functions
async function viewPlaybook(incidentId) {
    const modal = document.getElementById('playbook-modal');
    
    // Reset mitigation button state
    const btnMitigate = document.getElementById('btn-mitigate');
    const statusMsg = document.getElementById('mitigation-status');
    if(btnMitigate) {
        btnMitigate.style.backgroundColor = 'var(--danger)';
        btnMitigate.innerHTML = `<i class="fa-solid fa-ban"></i> Implement WAF Rule: Block IP (<span id="pb-mitigate-ip">...</span>)`;
        btnMitigate.disabled = false;
    }
    if(statusMsg) statusMsg.style.display = 'none';

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
            
            // Set mitigation targets
            const pbMitigateIpElement = document.getElementById('pb-mitigate-ip');
            if(pbMitigateIpElement) {
                pbMitigateIpElement.innerText = inc.source_ip;
                btnMitigate.dataset.ip = inc.source_ip;
            }
            
            const slaBanner = document.getElementById('pb-sla-banner');
            if (inc.severity === 'CRITICAL') {
                slaBanner.style.display = 'flex';
                slaBanner.style.backgroundColor = 'rgba(220, 38, 38, 0.15)';
                slaBanner.style.color = '#ef4444';
                slaBanner.style.border = '1px solid #ef4444';
                slaBanner.innerHTML = '<i class="fa-solid fa-radiation fa-spin"></i> <span><strong>CRITICAL SLA BREACH IMMINENT:</strong> IMMEDIATE RESPONSE REQUIRED ALONG WITH MITIGATION</span>';
            } else if (inc.severity === 'HIGH') {
                slaBanner.style.display = 'flex';
                slaBanner.style.backgroundColor = 'rgba(245, 158, 11, 0.15)';
                slaBanner.style.color = '#f59e0b';
                slaBanner.style.border = '1px solid #f59e0b';
                slaBanner.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> <span><strong>URGENT SLA:</strong> IMMEDIATE RESPONSE REQUIRED WITHIN 15 MINUTES</span>';
            } else {
                slaBanner.style.display = 'none';
            }

            
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

async function mitigateAttack() {
    const btn = document.getElementById('btn-mitigate');
    const ip = btn.dataset.ip;
    const statusMsg = document.getElementById('mitigation-status');
    
    statusMsg.style.display = 'block';
    statusMsg.style.color = '#f59e0b';
    statusMsg.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Implementing Firewall Rule...';
    btn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/mitigate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'block_ip', ip: ip })
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            statusMsg.style.color = '#10b981';
            statusMsg.innerHTML = `<i class="fa-solid fa-check-circle"></i> Active Defense Deployed: ${result.message}`;
            btn.style.backgroundColor = '#10b981';
            btn.style.borderColor = '#047857';
            btn.innerHTML = `<i class="fa-solid fa-shield-check"></i> IP Blocked at Perimeter`;
            
            // Optionally auto-check the playbook step if one exists for blocking
            document.querySelectorAll('.checklist-item label').forEach((label, idx) => {
                if(label.innerText.includes('Block')) {
                    document.getElementById(`step-${idx}`).checked = true;
                }
            });
        } else {
            throw new Error(result.message);
        }
    } catch (e) {
        statusMsg.style.color = '#ef4444';
        statusMsg.innerHTML = `<i class="fa-solid fa-xmark-circle"></i> Mitigation Failed: ${e}`;
        btn.disabled = false;
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
        filename:     `Prevention-Report-${document.getElementById('pb-id').innerText}.pdf`,
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
