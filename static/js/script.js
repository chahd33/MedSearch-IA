/**
 * MedSearch IA — Application frontend
 *
 * Communique avec le backend Flask via l'API REST.
 * Gère l'interface, les suggestions, la saisie vocale
 * et l'affichage des résultats.
 */

// ================================================================
// CONSTANTES
// ================================================================

const API_BASE = 'http://127.0.0.1:5000/api';

// ================================================================
// PROCESSEUR AUDIO (Web Speech API)
// ================================================================

class AudioProcessor {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this._init();
    }

    _init() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            throw new Error('Reconnaissance vocale non supportée par ce navigateur.');
        }
        this.recognition = new SR();
        this.recognition.lang = 'fr-FR';
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
    }

    start(onResult, onEnd) {
        if (!this.recognition || this.isListening) return;

        this.isListening = true;
        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            onResult(transcript, event.results[event.results.length - 1].isFinal);
        };
        this.recognition.onerror = (event) => {
            this.isListening = false;
            if (event.error !== 'no-speech') {
                throw new Error('Erreur vocale : ' + event.error);
            }
        };
        this.recognition.onend = () => {
            this.isListening = false;
            if (onEnd) onEnd();
        };
        this.recognition.start();
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        }
    }

    get supported() {
        return this.recognition !== null;
    }
}

// ================================================================
// GESTIONNAIRE D'INTERFACE
// ================================================================

class UIManager {
    constructor() {
        this.els = this._bindElements();
        this.currentMode = 'hybrid';
        this._setupEvents();
        this._initCellCanvas();
        this._loadStats();
    }

    _bindElements() {
        return {
            searchInput:   document.getElementById('searchInput'),
            searchBtn:     document.getElementById('searchBtn'),
            micBtn:        document.getElementById('micBtn'),
            suggestions:   document.getElementById('suggestions'),
            loaderArea:    document.getElementById('loaderArea'),
            resultsSection: document.getElementById('resultsSection'),
            resultsTitle:  document.getElementById('resultsTitle'),
            resultsList:   document.getElementById('resultsList'),
            webSection:    document.getElementById('webSection'),
            webList:       document.getElementById('webList'),
            emptyState:    document.getElementById('emptyState'),
            clearBtn:      document.getElementById('clearBtn'),
            statsDiseases: document.getElementById('statsDiseases'),
            statsSymptoms: document.getElementById('statsSymptoms'),
            statsMode:     document.getElementById('statsMode'),
            toastContainer: document.getElementById('toastContainer'),
            modePills:     document.querySelectorAll('.mode-pill'),
        };
    }

    _setupEvents() {
        // Recherche
        this.els.searchBtn.addEventListener('click', () => this._handleSearch());
        this.els.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._handleSearch();
        });

        // Suggestions
        this.els.searchInput.addEventListener('input', () => this._handleSuggestions());
        this.els.searchInput.addEventListener('focus', () => this._handleSuggestions());
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#searchWrap')) {
                this.els.suggestions.classList.remove('open');
            }
        });

        // Micro
        this.els.micBtn.addEventListener('click', () => this._handleAudio());

        // Modes
        this.els.modePills.forEach(pill => {
            pill.addEventListener('click', () => {
                this.els.modePills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.currentMode = pill.dataset.mode;
                this._updateModeLabel();
            });
        });

        // Effacer
        this.els.clearBtn.addEventListener('click', () => this._clearResults());
    }

    // --- Recherche ---
    async _handleSearch() {
        const query = this.els.searchInput.value.trim();
        if (!query) {
            this.showToast('Veuillez saisir au moins un symptôme', 'warning');
            this.els.searchInput.focus();
            return;
        }
        this.showLoader();
        try {
            const res = await fetch(
                `${API_BASE}/search?query=${encodeURIComponent(query)}&mode=${this.currentMode}`
            );
            const json = await res.json();
            if (json.error) {
                this.showToast(json.message, 'error');
                this.els.loaderArea.classList.add('hidden');
                this.els.emptyState.classList.remove('hidden');
                return;
            }
            this.displayResults(json.data);
        } catch (err) {
            this.showToast('Impossible de joindre le serveur. Vérifiez que le backend est lancé.', 'error');
            this.els.loaderArea.classList.add('hidden');
            this.els.emptyState.classList.remove('hidden');
        }
    }

    // --- Suggestions ---
    async _handleSuggestions() {
        const val = this.els.searchInput.value.trim();
        if (val.length < 2) {
            this.els.suggestions.classList.remove('open');
            return;
        }
        try {
            const res = await fetch(
                `${API_BASE}/suggestions?input=${encodeURIComponent(val)}`
            );
            const json = await res.json();
            if (json.error || !json.data.length) {
                this.els.suggestions.classList.remove('open');
                return;
            }

            this.els.suggestions.innerHTML = json.data.map(s => `
                <div class="suggestion-item" role="option" data-symptom="${s.symptom}">
                    <i class="fa-solid fa-${s.type === 'synonym' ? 'rotate' : 'tag'} text-med-accent text-xs mr-2"></i>
                    ${s.symptom}
                    <span class="cat-tag">${s.category}</span>
                </div>
            `).join('');

            this.els.suggestions.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', () => {
                    const current = this.els.searchInput.value.trim();
                    const sym = item.dataset.symptom;
                    const newVal = current
                        ? current.replace(/[, ]+$/, '') + ', ' + sym
                        : sym;
                    this.els.searchInput.value = newVal;
                    this.els.suggestions.classList.remove('open');
                    this.els.searchInput.focus();
                });
            });

            this.els.suggestions.classList.add('open');
        } catch (err) {
            this.els.suggestions.classList.remove('open');
        }
    }

    // --- Audio ---
    _handleAudio() {
        if (!this.audio) {
            this.showToast('Reconnaissance vocale non supportée. Utilisez Chrome ou Edge.', 'error');
            return;
        }
        if (this.audio.isListening) {
            this.audio.stop();
            this.els.micBtn.classList.remove('listening');
            this.showToast('Reconnaissance vocale arrêtée', 'info');
            return;
        }

        this.els.micBtn.classList.add('listening');
        this.showToast('Parlez maintenant...', 'info');

        try {
            this.audio.start(
                (transcript, isFinal) => {
                    this.els.searchInput.value = transcript;
                    if (isFinal) {
                        this.els.micBtn.classList.remove('listening');
                        this.showToast('Symptômes capturés avec succès', 'success');
                        setTimeout(() => this._handleSearch(), 300);
                    }
                },
                () => {
                    this.els.micBtn.classList.remove('listening');
                }
            );
        } catch (err) {
            this.els.micBtn.classList.remove('listening');
            this.showToast(err.message, 'error');
        }
    }

    // --- Affichage des résultats ---
    displayResults(searchResult) {
        const { results, query, mode, count } = searchResult;

        this.els.emptyState.classList.add('hidden');
        this.els.loaderArea.classList.add('hidden');

        if (count === 0) {
            this.els.resultsSection.classList.add('hidden');
            this.els.webSection.classList.add('hidden');
            this.els.emptyState.classList.remove('hidden');
            this.els.emptyState.innerHTML = `
                <div class="w-20 h-20 rounded-2xl bg-med-surface flex items-center justify-center mx-auto mb-5">
                    <i class="fa-solid fa-face-meh text-3xl text-med-amber"></i>
                </div>
                <p class="text-med-muted text-sm leading-relaxed">
                    Aucune pathologie correspondante trouvée pour :
                    <strong class="text-med-text">"${query}"</strong><br>
                    Essayez de formuler différemment vos symptômes.
                </p>`;
            this._loadWebLinks(query);
            return;
        }

        const modeLabels = {
            syntactic: 'Syntaxique (TF-IDF)',
            semantic:  'Sémantique (Ontologie)',
            hybrid:    'Hybride (TF-IDF + Ontologie)',
        };

        this.els.resultsTitle.innerHTML = `
            <span class="text-med-accent">${count}</span> résultat${count > 1 ? 's' : ''} trouvé${count > 1 ? 's' : ''}
            <span class="text-med-muted text-sm font-normal ml-2">— ${modeLabels[mode]}</span>`;

        const top = results.slice(0, 12);
        this.els.resultsList.innerHTML = top.map((r, i) => `
            <article class="result-card" style="animation-delay:${i * 60}ms"
                     aria-label="${r.disease} — Score ${r.scorePercent}%">
                <div class="flex items-start justify-between gap-4 mb-3">
                    <div>
                        <h3 class="font-semibold text-base">${r.disease}</h3>
                        <p class="text-xs text-med-muted mt-0.5">${r.matchRatio} symptômes correspondants</p>
                    </div>
                    <div class="text-right flex-shrink-0">
                        <span class="text-2xl font-bold font-display ${this._scoreClass(r.scorePercent)}">
                            ${r.scorePercent}%
                        </span>
                    </div>
                </div>
                <div class="score-bar-track mb-3">
                    <div class="score-bar-fill" style="width:0%" data-width="${r.scorePercent}%"></div>
                </div>
                <div class="flex flex-wrap gap-1.5">
                    ${r.matchedSymptoms.map(s =>
                        `<span class="sym-tag matched"><i class="fa-solid fa-check text-[9px]"></i>${s}</span>`
                    ).join('')}
                    ${r.unmatchedSymptoms.map(s =>
                        `<span class="sym-tag unmatched">${s}</span>`
                    ).join('')}
                </div>
            </article>
        `).join('');

        this.els.resultsSection.classList.remove('hidden');

        // Animer les barres de score
        requestAnimationFrame(() => {
            setTimeout(() => {
                document.querySelectorAll('.score-bar-fill').forEach(bar => {
                    bar.style.width = bar.dataset.width;
                });
            }, 100);
        });

        this._loadWebLinks(query);
    }

    _scoreClass(pct) {
        if (pct >= 70) return 'score-high';
        if (pct >= 40) return 'score-medium';
        return 'score-low';
    }

    // --- Liens web ---
    async _loadWebLinks(query) {
        try {
            const res = await fetch(
                `${API_BASE}/web-links?query=${encodeURIComponent(query)}`
            );
            const json = await res.json();
            if (json.error || !json.data.length) {
                this.els.webSection.classList.add('hidden');
                return;
            }

            this.els.webList.innerHTML = json.data.map(link => `
                <a href="${link.url}" target="_blank" rel="noopener noreferrer" class="web-card">
                    <div class="web-icon" style="background:${link.color}20; color:${link.color}">
                        <i class="${link.icon}"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="font-semibold text-sm">${link.name}</div>
                        <div class="text-xs text-med-muted truncate">${link.desc}</div>
                    </div>
                    <i class="fa-solid fa-arrow-up-right-from-square text-med-muted text-xs flex-shrink-0"></i>
                </a>
            `).join('');

            this.els.webSection.classList.remove('hidden');
        } catch (err) {
            this.els.webSection.classList.add('hidden');
        }
    }

    // --- Stats ---
    async _loadStats() {
        try {
            const res = await fetch(`${API_BASE}/stats`);
            const json = await res.json();
            if (!json.error) {
                this.els.statsDiseases.textContent = `${json.data.diseases} pathologies indexées`;
                this.els.statsSymptoms.textContent = `${json.data.symptoms} symptômes référencés`;
            }
        } catch (err) { /* silencieux */ }
        this._updateModeLabel();
    }

    _updateModeLabel() {
        const labels = { syntactic: 'Syntaxique', semantic: 'Sémantique', hybrid: 'Hybride' };
        this.els.statsMode.textContent = 'Mode : ' + (labels[this.currentMode] || this.currentMode);
    }

    // --- Utilitaires UI ---
    _clearResults() {
        this.els.resultsSection.classList.add('hidden');
        this.els.webSection.classList.add('hidden');
        this.els.searchInput.value = '';
        this.els.emptyState.classList.remove('hidden');
        this.els.emptyState.innerHTML = `
            <div class="w-20 h-20 rounded-2xl bg-med-surface flex items-center justify-center mx-auto mb-5">
                <i class="fa-solid fa-heart-pulse text-3xl text-med-muted"></i>
            </div>
            <p class="text-med-muted text-sm leading-relaxed">
                Décrivez vos symptômes ci-dessus pour obtenir un diagnostic probabiliste.
                Vous pouvez aussi utiliser le microphone pour une saisie vocale.
            </p>`;
        this.els.searchInput.focus();
    }

    showLoader() {
        this.els.resultsSection.classList.add('hidden');
        this.els.webSection.classList.add('hidden');
        this.els.emptyState.classList.add('hidden');
        this.els.loaderArea.classList.remove('hidden');
    }

    showToast(message, type = 'info') {
        const icons = {
            info: 'fa-circle-info', success: 'fa-circle-check',
            error: 'fa-circle-xmark', warning: 'fa-triangle-exclamation',
        };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fa-solid ${icons[type]}"></i><span>${message}</span>`;
        this.els.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'toastOut 0.3s ease-in forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // --- Canvas cellules animé ---
    _initCellCanvas() {
        const canvas = document.getElementById('cell-canvas');
        const ctx = canvas.getContext('2d');
        let cells = [];

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        for (let i = 0; i < 30; i++) {
            cells.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: Math.random() * 20 + 8,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                opacity: Math.random() * 0.04 + 0.01,
                hue: Math.random() > 0.5 ? 160 : 170,
            });
        }

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            cells.forEach(c => {
                c.x += c.vx;
                c.y += c.vy;
                if (c.x < -30) c.x = canvas.width + 30;
                if (c.x > canvas.width + 30) c.x = -30;
                if (c.y < -30) c.y = canvas.height + 30;
                if (c.y > canvas.height + 30) c.y = -30;

                ctx.beginPath();
                ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
                ctx.fillStyle = `hsla(${c.hue}, 70%, 50%, ${c.opacity})`;
                ctx.fill();

                ctx.beginPath();
                ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
                ctx.strokeStyle = `hsla(${c.hue}, 70%, 50%, ${c.opacity * 1.5})`;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            });
            requestAnimationFrame(animate);
        };
        animate();
    }
}

// ================================================================
// DÉMARRAGE
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    const ui = new UIManager();

    // Initialisation du processeur audio
    try {
        ui.audio = new AudioProcessor();
        if (!ui.audio.supported) {
            document.getElementById('micBtn').style.opacity = '0.3';
            document.getElementById('micBtn').title = 'Vocale non supportée';
        }
    } catch (err) {
        console.warn('Audio indisponible:', err.message);
        ui.audio = { supported: false, isListening: false, stop() {} };
        document.getElementById('micBtn').style.opacity = '0.3';
    }
});