const API_BASE = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    setupNavigation();
    loadDashboardData();
    
    document.getElementById("btn-optimize").addEventListener("click", runOptimization);
});

function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-links li");
    const panes = document.querySelectorAll(".tab-pane");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            navItems.forEach(n => n.classList.remove("active"));
            panes.forEach(p => p.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(item.dataset.target).classList.add("active");
        });
    });
}

async function loadDashboardData() {
    loadComparison();
    loadFeedbackTimeline();
    loadStocks();
    loadBacktest();
}

async function loadBacktest() {
    try {
        const res = await fetch(`${API_BASE}/backtest`);
        const data = await res.json();
        
        Plotly.newPlot("backtest-chart", [
            {x: data.dates, y: data.E0, name: 'E0 (Equal Weight Baseline)', type: 'scatter', line: {color: '#94a3b8'}},
            {x: data.dates, y: data.E6, name: 'E6 (ML Best Champion)', type: 'scatter', line: {color: '#10b981', width: 3}}
        ], {
            paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
            font: {color: '#94a3b8'},
            yaxis: {title: 'Cumulative Equity', gridcolor: 'rgba(255,255,255,0.05)'},
            xaxis: {gridcolor: 'rgba(255,255,255,0.05)'},
            margin: {t: 20, l: 50, r: 20, b: 40}
        }, {responsive: true});
    } catch (e) {
        console.error(e);
    }
}

async function loadComparison() {
    try {
        const res = await fetch(`${API_BASE}/model-comparison`);
        const data = await res.json();
        
        if(data.experiments && data.experiments.length > 0) {
            // Render Chart
            const x = data.experiments.map(e => e.experiment);
            const y = data.experiments.map(e => e.sharpe);
            
            Plotly.newPlot("comparison-chart", [{
                x: x, y: y, type: 'bar', 
                marker: { color: 'rgba(59, 130, 246, 0.8)', line: {color: '#3b82f6', width: 1} }
            }], {
                paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
                font: {color: '#94a3b8'},
                yaxis: {title: 'Sharpe Ratio', gridcolor: 'rgba(255,255,255,0.05)'},
                xaxis: {gridcolor: 'rgba(255,255,255,0.05)'},
                margin: {t: 20, l: 50, r: 20, b: 40}
            }, {responsive: true});

            // Populate Overview Tab Metrics
            const best = data.experiments.reduce((max, obj) => obj.sharpe > max.sharpe ? obj : max, data.experiments[0]);
            document.getElementById("overview-metrics").innerHTML = `
                <div class="metric-card"><h4>Top Performing Model</h4><div class="val">${best.experiment}</div></div>
                <div class="metric-card"><h4>Max Sharpe Ratio</h4><div class="val">${best.sharpe.toFixed(3)}</div></div>
                <div class="metric-card"><h4>Annual Return</h4><div class="val">${(best.annual_return*100).toFixed(2)}%</div></div>
                <div class="metric-card"><h4>Max Drawdown</h4><div class="val" style="color:#ef4444">${(best.max_drawdown*100).toFixed(2)}%</div></div>
            `;
        }
    } catch (e) {
        console.error("API error", e);
    }
}

async function loadFeedbackTimeline() {
    try {
        const res = await fetch(`${API_BASE}/champion-challenger`);
        const data = await res.json();
        
        if (data.length === 0) return;

        let html = '';
        data.forEach(item => {
            const statusClass = item.decision === 'PROMOTED' ? 'status-promoted' : (item.decision === 'REJECTED' ? 'status-rejected' : '');
            html += `
                <div class="timeline-item">
                    <div style="color: #94a3b8; font-size: 0.9em; margin-bottom: 5px;">${item.date || 'Evaluation Event'}</div>
                    <div style="font-size: 1.1em; margin-bottom: 8px;">
                        Champion (${item.champion_version}) vs Challenger (${item.challenger_version})
                    </div>
                    <div>Decision: <span class="${statusClass}">${item.decision}</span></div>
                    <div style="color: #cbd5e1; font-size: 0.95em; margin-top: 5px;">Reason: ${item.reason}</div>
                </div>
            `;
        });
        document.getElementById("feedback-timeline").innerHTML = html;
    } catch(e) {
        console.error(e);
    }
}

async function loadStocks() {
    try {
        const res = await fetch(`${API_BASE}/stocks`);
        const stocks = await res.json();
        const html = stocks.map(s => `
            <div class="metric-card">
                <h4 style="color: #fff">${s.symbol}</h4>
                <div class="val" style="font-size:1.1em; color:#94a3b8;">${s.sector}</div>
            </div>
        `).join('');
        document.getElementById("stock-list").innerHTML = `<div class="grid-metrics">${html}</div>`;
    } catch (e) {
        console.error(e);
    }
}

async function runOptimization() {
    const btn = document.getElementById("btn-optimize");
    btn.innerText = "Running Optimization...";
    try {
        const res = await fetch(`${API_BASE}/portfolio/optimize`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({strategy: "max_sharpe", w_max: 0.40})
        });
        const data = await res.json();
        
        let html = `
            <h3 style="margin-top:0;">Allocation Strategy: ${data.strategy}</h3>
            <p style="color:#94a3b8;">Expected Return: <strong style="color:#fff">${(data.expected_return*100).toFixed(2)}%</strong> 
            | Volatility: <strong style="color:#fff">${(data.volatility*100).toFixed(2)}%</strong></p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">
            <ul style="list-style:none; padding:0;">
        `;
        data.weights.forEach(w => {
            const capText = w.max_cap_hit ? '<span style="color:#f59e0b; font-size:0.85em; margin-left: 10px;">(Cap Limit Reached)</span>' : '';
            html += `
                <li style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <strong style="display:inline-block; width:100px;">${w.symbol}</strong> 
                    <span style="color: #3b82f6; font-weight:600;">${(w.weight*100).toFixed(1)}%</span>
                    ${capText}
                </li>
            `;
        });
        html += "</ul>";
        document.getElementById("optimizer-results").innerHTML = html;
    } catch (e) {
        console.error(e);
        document.getElementById("optimizer-results").innerHTML = "<p style='color:red;'>Optimization failed. Is the API running?</p>";
    }
    btn.innerText = "Run Max Sharpe Optimization";
}
