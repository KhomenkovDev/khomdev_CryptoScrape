document.addEventListener('DOMContentLoaded', () => {
    // ── DOM refs ──────────────────────────────────────────────────────────
    const analyzeBtn          = document.getElementById('analyze-btn');
    const brandInput          = document.getElementById('brand-name');
    const competitorInput     = document.getElementById('competitor-name');
    const loader              = document.getElementById('loader');
    const resultsArea         = document.getElementById('results-area');
    const platformResultsGrid = document.getElementById('platform-results');
    const suggestionsList     = document.getElementById('suggestions-list');
    const roadmapList         = document.getElementById('marketing-roadmap-list');
    const competitorBox       = document.getElementById('competitor-box');
    const competitorContent   = document.getElementById('competitor-content');
    const displayBrandName    = document.getElementById('display-brand-name');
    const sentimentText       = document.getElementById('overall-sentiment-text');
    const gaugeValue          = document.getElementById('gauge-score');
    const demoBadge           = document.getElementById('demo-badge');
    const toggleBtn           = document.getElementById('social-accounts-toggle');
    const accountsBody        = document.getElementById('social-accounts-body');
    const toggleArrow         = document.getElementById('toggle-arrow');

    // Brand search refs
    const suggestionsBox  = document.getElementById('brand-suggestions');
    const brandInfoCard   = document.getElementById('brand-info-card');
    const brandInfoThumb  = document.getElementById('brand-info-thumb');
    const brandInfoTitle  = document.getElementById('brand-info-title');
    const brandInfoDesc   = document.getElementById('brand-info-desc');
    const brandInfoExtract= document.getElementById('brand-info-extract');
    const brandInfoUrl    = document.getElementById('brand-info-url');
    const brandClearBtn   = document.getElementById('brand-clear-btn');

    let sentimentChart   = null;
    let searchDebounce   = null;
    let activeIndex      = -1;   // keyboard nav index in dropdown
    let selectedBrand    = null; // the confirmed brand name after picking

    console.log("BrandMonitor: Client script initialized.");
    checkSocialStatus();

    // ── Brand & Competitor Autocomplete ─────────────────────────────────
    function setupAutocomplete(inputEl, suggestionsBox, clearBtn, onSelect) {
        let debounceTimer = null;
        let activeIdx = -1;

        inputEl.addEventListener('input', () => {
            const q = inputEl.value.trim();
            if (clearBtn) clearBtn.style.display = q ? 'flex' : 'none';
            
            if (q.length < 2) {
                hideBox();
                return;
            }

            clearTimeout(debounceTimer);
            suggestionsBox.innerHTML = '<div class="suggestion-searching">Searching...</div>';
            suggestionsBox.style.display = 'block';

            debounceTimer = setTimeout(() => fetchResults(q), 300);
        });

        inputEl.addEventListener('keydown', (e) => {
            const items = suggestionsBox.querySelectorAll('.suggestion-item');
            if (!items.length) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIdx = (activeIdx + 1) % items.length;
                updateActive(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIdx = (activeIdx - 1 + items.length) % items.length;
                updateActive(items);
            } else if (e.key === 'Enter' && activeIdx > -1) {
                e.preventDefault();
                items[activeIdx].click();
            } else if (e.key === 'Escape') {
                hideBox();
            }
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                inputEl.value = '';
                inputEl.focus();
                clearBtn.style.display = 'none';
                hideBox();
                if (onSelect) onSelect(null);
            });
        }

        async function fetchResults(q) {
            try {
                const res = await fetch(`/brand/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                renderBox(data);
            } catch (err) {
                suggestionsBox.innerHTML = '<div class="suggestion-error">Search failed.</div>';
            }
        }

        function renderBox(suggestions) {
            if (!suggestions.length) {
                suggestionsBox.innerHTML = '<div class="suggestion-item no-results">No results found.</div>';
                suggestionsBox.style.display = 'block';
                return;
            }

            suggestionsBox.innerHTML = suggestions.map((s, i) => `
                <div class="suggestion-item ${s.is_brand ? 'is-brand' : ''}" data-index="${i}" data-title="${s.title}">
                    <div class="suggestion-header">
                        <span class="suggestion-title">${s.title}</span>
                        ${s.is_brand ? '<span class="brand-badge-small">Brand</span>' : ''}
                    </div>
                    <span class="suggestion-desc">${s.description || 'Global Entity'}</span>
                </div>
            `).join('');

            suggestionsBox.style.display = 'block';
            activeIdx = -1;

            suggestionsBox.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', () => {
                    const title = item.getAttribute('data-title');
                    inputEl.value = title;
                    hideBox();
                    if (onSelect) onSelect(title);
                });
            });
        }

        function updateActive(items) {
            items.forEach((item, i) => {
                item.classList.toggle('active', i === activeIdx);
                if (i === activeIdx) item.scrollIntoView({ block: 'nearest' });
            });
        }

        function hideBox() {
            suggestionsBox.style.display = 'none';
            suggestionsBox.innerHTML = '';
            activeIdx = -1;
        }
    }

    setupAutocomplete(brandInput, suggestionsBox, brandClearBtn, (title) => {
        if (title) {
            selectedBrand = title;
            fetchBrandInfo(title);
        } else {
            brandInfoCard.style.display = 'none';
            selectedBrand = null;
        }
    });

    const compSuggestionsBox = document.getElementById('competitor-suggestions');
    const compClearBtn = document.getElementById('competitor-clear-btn');
    if (competitorInput && compSuggestionsBox) {
        setupAutocomplete(competitorInput, compSuggestionsBox, compClearBtn, null);
    }

    async function fetchBrandInfo(name) {
        console.log(`BrandMonitor: Fetching info for "${name}"...`);
        try {
            const res = await fetch(`/brand/info?name=${encodeURIComponent(name)}`);
            if (!res.ok) throw new Error('Not found');
            const data = await res.json();
            console.log("BrandMonitor: Brand info received:", data.title);
            
            brandInfoTitle.textContent = data.title;
            brandInfoDesc.textContent  = data.description || 'Global Brand';
            brandInfoExtract.textContent = data.extract;
            
            if (data.thumbnail) {
                brandInfoThumb.src = data.thumbnail;
                brandInfoThumb.style.display = 'block';
            } else {
                brandInfoThumb.style.display = 'none';
            }
            
            brandInfoUrl.href = data.url;
            brandInfoCard.style.display = 'flex';
        } catch (err) {
            brandInfoCard.style.display = 'none';
        }
    }

    // ── Social accounts panel toggle ──────────────────────────────────────
    toggleBtn.addEventListener('click', () => {
        const isOpen = accountsBody.classList.toggle('open');
        toggleArrow.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
    });

    // ── Social status poll ────────────────────────────────────────────────
    async function checkSocialStatus() {
        try {
            const res  = await fetch('/social/status');
            const data = await res.json();
            updatePlatformUI('x',         data.x);
            updatePlatformUI('instagram', data.instagram);
        } catch (_) { /* server not running yet */ }
    }

    function updatePlatformUI(platform, connected) {
        const isX     = platform === 'x';
        const prefix  = isX ? 'x' : 'ig';
        const label   = isX ? 'X (Twitter)' : 'Instagram';

        // Pill in header
        const pill    = document.getElementById(`${prefix}-status-pill`);
        const dot     = pill.querySelector('.pill-dot');
        dot.className = `pill-dot ${connected ? 'connected' : 'disconnected'}`;
        pill.title    = connected ? `${label}: session active` : `${label}: not connected`;

        // Card state
        const form        = document.getElementById(`${prefix}-form`);
        const connectedMsg= document.getElementById(`${prefix}-connected-msg`);
        const connLabel   = document.getElementById(`${prefix}-connection-label`);
        const disconnBtn  = document.getElementById(`${prefix}-disconnect-btn`);

        if (connected) {
            form.style.display         = 'none';
            connectedMsg.style.display = 'flex';
            disconnBtn.style.display   = 'inline-flex';
            connLabel.textContent      = 'Connected ✓';
            connLabel.style.color      = 'var(--success)';
        } else {
            form.style.display         = 'flex';
            connectedMsg.style.display = 'none';
            disconnBtn.style.display   = 'none';
            connLabel.textContent      = 'Not connected';
            connLabel.style.color      = 'var(--text-secondary)';
        }

        // Dim the checkbox if not connected
        const checkboxLabel = document.getElementById(`${prefix === 'x' ? 'x' : 'ig'}-checkbox-label`);
        if (checkboxLabel) {
            checkboxLabel.style.opacity = connected ? '1' : '0.5';
            const cb = checkboxLabel.querySelector('input[type=checkbox]');
            if (cb && !connected) cb.checked = false;
        }
    }

    // ── Connect a platform (called from HTML onclick) ─────────────────────
    window.connectPlatform = async function(platform) {
        const isX      = platform === 'x';
        const prefix   = isX ? 'x' : 'ig';
        const username = document.getElementById(`${prefix}-username`).value.trim();
        const password = document.getElementById(`${prefix}-password`).value;

        if (!username || !password) {
            showToast('Please enter both username and password.', 'warning');
            return;
        }

        const connectBtn = document.getElementById(`${prefix}-connect-btn`);
        const btnText    = connectBtn.querySelector('.btn-text');
        const btnSpinner = connectBtn.querySelector('.btn-spinner');

        connectBtn.disabled   = true;
        btnText.textContent   = 'Opening browser…';
        btnSpinner.style.display = 'inline-block';

        showToast(`A browser window will open. Log in and complete any CAPTCHA — the session will be saved automatically.`, 'info', 8000);

        try {
            const res = await fetch('/social/connect', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ platform, username, password })
            });

            const data = await res.json();

            if (!res.ok) {
                showToast(`Login failed: ${data.detail}`, 'error');
            } else {
                showToast(data.message, 'success');
                // Clear sensitive fields
                document.getElementById(`${prefix}-password`).value = '';
                await checkSocialStatus();
            }
        } catch (err) {
            showToast('Connection error: ' + err.message, 'error');
        } finally {
            connectBtn.disabled      = false;
            btnText.textContent      = isX ? 'Connect X Account' : 'Connect Instagram Account';
            btnSpinner.style.display = 'none';
        }
    };

    // ── Disconnect a platform (called from HTML onclick) ──────────────────
    window.disconnectPlatform = async function(platform) {
        try {
            await fetch(`/social/disconnect/${platform}`, { method: 'DELETE' });
            showToast(`Disconnected from ${platform === 'x' ? 'X' : 'Instagram'}.`, 'info');
            await checkSocialStatus();
        } catch (err) {
            showToast('Error: ' + err.message, 'error');
        }
    };

    // ── Analyze ───────────────────────────────────────────────────────────
    analyzeBtn.addEventListener('click', async () => {
        const brandName        = brandInput.value.trim();
        const competitorName   = competitorInput.value.trim();
        const selectedPlatforms = Array.from(
            document.querySelectorAll('input[name="platform"]:checked')
        ).map(cb => cb.value);

        if (!brandName) { showToast('Please enter a target brand name.', 'warning'); return; }
        if (selectedPlatforms.length === 0) { showToast('Select at least one platform.', 'warning'); return; }

        // Reset UI
        analyzeBtn.disabled      = true;
        analyzeBtn.textContent   = 'ANALYZING...';
        loader.style.display     = 'block';
        resultsArea.style.display = 'none';
        platformResultsGrid.innerHTML = '';
        suggestionsList.innerHTML     = '';
        roadmapList.innerHTML         = '';
        competitorBox.style.display   = 'none';

        try {
            const response = await fetch('/analyze', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({
                    brand_name:      brandName,
                    platforms:       selectedPlatforms,
                    competitor_name: competitorName || null
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Analysis failed');
            }

            const data = await response.json();
            renderResults(data);
        } catch (error) {
            console.error(error);
            showToast('Analysis error: ' + error.message, 'error');
        } finally {
            loader.style.display   = 'none';
            analyzeBtn.disabled    = false;
            analyzeBtn.textContent = 'GENERATE REPUTATION REPORT';
        }
    });

    // ── Render results ────────────────────────────────────────────────────
    function renderResults(data) {
        displayBrandName.textContent = data.brand_name;
        sentimentText.textContent    = `Overall Sentiment: ${data.overall_sentiment}`;
        gaugeValue.textContent       = Math.round(data.sentiment_score);
        updateGauge(data.sentiment_score);

        // Platform cards
        Object.entries(data.platform_reports).forEach(([platform, report], index) => {
            const card = document.createElement('div');
            card.className = 'glass-card result-card';
            card.style.animationDelay = `${index * 0.1}s`;

            const platformLabel = {
                google: '🔍 Google Reviews',
                news:   '📰 Web News',
                x:      '𝕏 X (Twitter)',
                instagram: '📸 Instagram',
            }[platform] || platform;

            card.innerHTML = `
                <div class="platform-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                    <h3 style="text-transform: capitalize;">${platformLabel}</h3>
                    <div class="score-badge ${report.label.toLowerCase()}">${report.score}% ${report.label}</div>
                </div>
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6; font-size: 0.95rem;">${report.summary}</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <h4 style="color: var(--success); font-size: 0.8rem; margin-bottom: 0.5rem; letter-spacing:1px;">STRENGTHS</h4>
                        <ul style="list-style: none; font-size: 0.85rem; color: var(--text-secondary);">
                            ${report.strengths.map(s => `<li>• ${s}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <h4 style="color: var(--danger); font-size: 0.8rem; margin-bottom: 0.5rem; letter-spacing:1px;">WEAKNESSES</h4>
                        <ul style="list-style: none; font-size: 0.85rem; color: var(--text-secondary);">
                            ${report.weaknesses.map(w => `<li>• ${w}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
            platformResultsGrid.appendChild(card);
            setTimeout(() => card.classList.add('visible'), 50);
        });

        // Competitor
        if (data.competitor_analysis) {
            competitorBox.style.display = 'block';
            competitorContent.innerHTML = `
                <div style="margin-bottom: 2rem;">
                    <div class="status-row">
                        <strong>Competitor:</strong>
                        <span>${data.competitor_analysis.competitor_name}</span>
                    </div>
                    <div class="status-row">
                        <strong>Status:</strong>
                        <span class="score-badge ${data.competitor_analysis.relative_sentiment === 'Better' ? 'positive' : 'negative'}">
                            ${data.competitor_analysis.relative_sentiment} than Competitor
                        </span>
                    </div>
                </div>
                <p style="font-size: 0.95rem; line-height: 1.7; color: var(--text-primary);">${data.competitor_analysis.competitive_advantage}</p>
                <div class="status-row" style="margin-top: 1.5rem;">
                    <strong style="font-size: 0.8rem; color: var(--text-secondary);">Market Threat:</strong>
                    <span class="score-badge ${data.competitor_analysis.threat_level.toLowerCase() === 'high' ? 'negative' : (data.competitor_analysis.threat_level.toLowerCase() === 'medium' ? 'neutral' : 'positive')}" style="padding: 0.2rem 0.8rem; font-size: 0.75rem;">
                        ${data.competitor_analysis.threat_level}
                    </span>
                </div>
            `;
        }

        // Roadmap
        data.marketing_roadmap.forEach(task => {
            const item = document.createElement('div');
            item.className = `task-item ${task.priority.toLowerCase()}`;
            item.innerHTML = `
                <h4 style="font-size: 1rem; margin-bottom: 0.3rem;">${task.title}</h4>
                <p style="font-size: 0.9rem; color: var(--text-secondary);">${task.description}</p>
                <div class="task-meta">
                    <span>Priority: ${task.priority}</span>
                    <span>Category: ${task.category}</span>
                </div>
            `;
            roadmapList.appendChild(item);
        });

        // Insights
        data.strategic_suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerHTML = `<p style="font-size: 1rem;">${suggestion}</p>`;
            suggestionsList.appendChild(item);
        });

        resultsArea.style.display = 'block';
        resultsArea.scrollIntoView({ behavior: 'smooth' });
    }

    // ── Gauge chart ───────────────────────────────────────────────────────
    function updateGauge(score) {
        const ctx   = document.getElementById('sentimentChart').getContext('2d');
        if (sentimentChart) sentimentChart.destroy();
        const color = score > 70 ? '#00ff88' : (score > 40 ? '#ffcc00' : '#ff4d4d');

        sentimentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [color, 'rgba(255,255,255,0.05)'],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270,
                    borderRadius: 10
                }]
            },
            options: {
                cutout: '80%',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } }
            }
        });
    }

    // ── Toast notification ────────────────────────────────────────────────
    function showToast(message, type = 'info', duration = 4000) {
        const existing = document.getElementById('toast-notification');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.id        = 'toast-notification';
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span>${message}</span>`;
        document.body.appendChild(toast);

        requestAnimationFrame(() => toast.classList.add('toast-visible'));
        setTimeout(() => {
            toast.classList.remove('toast-visible');
            setTimeout(() => toast.remove(), 400);
        }, duration);
    }
});
