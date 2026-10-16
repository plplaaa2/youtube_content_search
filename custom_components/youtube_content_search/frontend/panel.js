// YouTube Content Search Web Component
class YouTubeContentSearchPanel extends HTMLElement {
    static get observedAttributes() {
        return ['external-network', 'config-attributes'];
    }

    constructor() {
        super();
        this._config = {};
        this._hass = null;
        this._initConfig();
    }

    connectedCallback() {
        if (this.shadowRoot) return;
        this.attachShadow({ mode: 'open' });
        this.render();

        // Listen for HASS events
        window.addEventListener('message', this._handleMessage.bind(this));
        window.__hass = this._hass || {};
    }

    disconnectedCallback() {
        if (this.shadowRoot) return;
        window.removeEventListener('message', this._handleMessage.bind(this));
    }

    attributeChangedCallback(name, oldVal, newVal) {
        if (name === 'external-network' && newVal !== oldVal) {
            // Could be used for cross-origin loading
        }
    }

    _initConfig() {
        this._config = JSON.parse(this.getAttribute('config-attributes') || '{}');
    }

    render() {
        const root = this.shadowRoot;
        if (!root) return;

        // Inject styles
        const style = document.createElement('style');
        style.textContent = `
            :host { display: block; }
            #app { max-width: 1400px; margin: 0 auto; min-height: 100vh; padding-top: 60px; }
            
            .header { display: flex; justify-content: space-between; align-items: center; padding: 20px 32px; background-color: var(--card-surface, #1e1e1e); border-bottom: 1px solid rgba(255,255,255,0.06); }
            .header-left { display: flex; align-items: center; gap: 12px; }
            
            .logo-text { font-size: 24px; font-weight: bold; white-space: nowrap; }
            
            .tab-nav { display: flex; gap: 4px; background: transparent; padding: 0; border-radius: 8px; margin-left: auto; }
            .tab-btn { background: rgba(255,255,255,0.06); color: var(--text-secondary, #aaaaaa); border: none; padding: 10px 24px; cursor: pointer; font-size: 13px; font-weight: 500; border-radius: 8px; display: flex; align-items: center; gap: 6px; transition: all .2s; }
            .tab-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
            .tab-btn.active { background: var(--primary-color, #3ea6ff); color: #fff; }

            .tab-content { display: none; padding: 24px 32px; min-height: calc(100vh - 76px); }
            .tab-content.active { display: block; }

            .section-title { font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #fff; }

            .search-bar { display: flex; gap: 12px; background: var(--card-surface, #1e1e1e); border-radius: 36px; padding: 8px 16px; max-width: 900px; margin-bottom: 24px; }
            .search-bar input { flex: 1; background: none; border: none; color: #fff; font-size: 16px; outline: none; padding-right: 8px; }
            .search-btn { background: var(--primary-color, #3ea6ff); color: #fff; border: none; padding: 12px 20px; border-radius: 28px; cursor: pointer; font-size: 14px; transition: opacity .2s; }
            .search-btn:hover { opacity: 0.9; }

            .video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }
            .video-card { background: var(--card-surface, #1e1e1e); border-radius: 12px; overflow: hidden; cursor: pointer; transition: transform .2s, box-shadow .2s; display: flex; flex-direction: column; }
            .video-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.5); }
            .video-thumbnail-wrapper { position: relative; width: 100%; height: 200px; background: #000; }
            .video-duration-overlay { position: absolute; bottom: 8px; right: 8px; padding: 3px 6px; background: rgba(0,0,0,.8); border-radius: 4px; font-size: 12px; color: #fff; display: flex; align-items: center; gap: 4px; }
            .video-card-body { padding: 12px 16px; flex: 1; display: flex; flex-direction: column; }
            .video-title { font-size: 15px; font-weight: bold; line-height: 1.3; margin-bottom: 8px; word-break: break-word; }

            .empty-state { display: flex; align-items: center; justify-content: center; padding: 80px 20px; text-align: center; color: var(--text-secondary, #aaaaaa); font-size: 15px; }

            /* Playlist */
            .playlists-list { display: grid; gap: 16px; }
            .playlist-item { background: var(--card-surface, #1e1e1e); border-radius: 10px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: all .2s; }
            .playlist-item:hover { background: rgba(255,255,255,.08); }

            /* Settings */
            .setting-group { background: var(--card-surface, #1e1e1e); border-radius: 12px; padding: 24px; margin-bottom: 16px; }
            .input-field { background: rgba(0,0,0,.3); border: 1px solid rgba(255,255,255,.12); color: #fff; padding: 10px 14px; border-radius: 8px; width: 100%; font-size: 14px; outline: none; transition: border-color .2s; }
            .input-field:focus { border-color: var(--primary-color, #3ea6ff); }

            /* Modal */
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 2000; background: rgba(0,0,0,.75); display: flex; align-items: center; justify-content: center; }
            .modal-overlay.hidden { display: none; }
            .modal { background: var(--card-surface, #1e1e1e); border-radius: 12px; width: 90%; max-width: 640px; box-shadow: 0 8px 32px rgba(0,0,0,.6); animation: fadeIn .2s ease; overflow-y: auto; max-height: 90vh; }
            @keyframes fadeIn { from { opacity: 0; transform: scale(.95); } to { opacity: 1; transform: scale(1); } }

            /* Toast */
            .toast-container { position: fixed; bottom: 32px; right: 32px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
            .toast-msg { padding: 12px 20px; border-radius: 8px; font-size: 14px; color: #fff; animation: slideUp .3s ease; max-width: 400px; text-align: center; line-height: 1.5; }
            .toast-msg.success { background: #2e7d32; }
            .toast-msg.error { background: #c62828; }
            @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

            /* Scrollbar */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-thumb { background: rgba(255,255,255,.2); border-radius: 4px; }

            /* Responsive */
            @media (max-width: 900px) {
                .header { padding: 16px 16px; flex-wrap: wrap; gap: 12px; }
                .tab-nav { width: 100%; display: flex; overflow-x: auto; justify-content: center; -webkit-overflow-scrolling: touch; }
                #app { padding-bottom: 60px; }
            }

            /* Utility */
            [hidden] { display: none !important; }
        `;
        root.appendChild(style);

        // Build DOM elements once
        this._root = root;
        this._tabsEl = root.querySelector('.tab-nav');
        this._searchInput = root.querySelector('#search-input');
        this._searchBtn = root.querySelector('#search-btn');
        this._emptyState = root.querySelector('#empty-state');
        this._videoGrid = root.querySelector('#video-grid');
        this._playerArea = root.querySelector('#player-area');
        this._playlistsList = root.querySelector('#playlists-list');
        this._settingsForm = root.querySelector('#settings-form');
        this._toastContainer = root.querySelector('#toast-container');

        // Set up tab switching
        if (this._tabsEl) {
            this._tabsEl.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
            });
        }

        // Set up search button
        if (this._searchBtn && this._searchInput) {
            this._searchBtn.addEventListener('click', () => this.handleSearch());
            this._searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') this.handleSearch();
            });
        }

        // Set up toast container
        this._toastContainer = root.querySelector('#toast-container');
    }

    async _handleMessage(event) {
        const data = event.data;
        if (!data || !this._hass) return;

        if (data.hass && this._config.asyncSetup !== false) {
            this._hass = data.hass;
        }

        // Handle service calls from HA
        if (data.serviceCall) {
            await this.handleServiceCall(data.serviceCall);
        }

        // Handle config updates
        if (data.configUpdate) {
            this._config = data.configUpdate;
        }
    }

    switchTab(tabId) {
        const tabs = this._tabsEl.querySelectorAll('.tab-btn');
        const contents = this._root.querySelectorAll('.tab-content');
        
        tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
        contents.forEach(c => c.classList.toggle('active', c.id === 'tab-' + tabId || c.querySelector('#tab-' + tabId)));

        if (tabId === 'settings') {
            this.showSettingsView();
        } else if (tabId === 'playlist') {
            this.showPlaylistView();
        }
    }

    async handleSearch() {
        const query = this._searchInput?.value.trim();
        if (!query) return this.showToast('검색어를 입력해주세요', 'error');

        this._emptyState.classList.remove('active');
        this._videoGrid.classList.add('active');
        this._playerArea.classList.add('hidden');

        try {
            const api = window.__hass?.api?.base_url;
            if (!api) throw new Error('HA API base URL not available');

            const res = await fetch(`${api}/youtube-search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const results = await res.json();
            this.renderSearchGrid(results);
        } catch (e) {
            console.error('Search error:', e);
            this.showToast('검색 실패: ' + e.message, 'error');
        }
    }

    renderSearchGrid(results) {
        if (!results.length) return;
        
        const html = results.map(v => `
            <div class="video-card" data-id="${v.id}" onclick="window.__yocsPanel.playVideo('${v.id}', '${this._escapeHtml(v.title)}')">
                <div class="video-thumbnail-wrapper">
                    ${v.thumbnails?.[0]?.url 
                        ? `<img src="${v.thumbnails[0].url}" alt="" class="video-thumbnail" loading="lazy"/>` : ''}
                </div>
                <div class="video-card-body">
                    <h3 class="video-title">${this._escapeHtml(v.title)}</h3>
                </div>
            </div>`).join('');

        this._videoGrid.innerHTML = html;
    }

    playVideo(videoId, title) {
        this._playerArea.innerHTML = `
            <iframe src="https://www.youtube.com/embed/${videoId}?autoplay=1" allowfullscreen loading="lazy"></iframe>
            <div class="player-info-bar">
                <span><strong>${this._escapeHtml(title)}</strong></span>
                <a href="https://www.youtube.com/watch?v=${videoId}" target="_blank">▶ 외부 재생</a>
            </div>`;
        this._playerArea.classList.remove('hidden');

        // Reset playlist selection when playing
        window.__yocsPanel.selectedPlaylistId = null;
    }

    showOpenPlaylistModal() {
        const modalInner = this._root.querySelector('#playlist-modal .modal');
        if (!modalInner) return;

        let html = '<ul class="playlist-item">';
        
        // Show existing playlists or empty state
        if (Object.keys(window.__yocsPanel.playlists || {}).length === 0) {
            html += '<li style="padding:16px;color:#aaa;text-align:center;">저장된 플레이리스트가 없습니다.</li>';
        } else {
            const playlistIds = Object.keys(window.__yocsPanel.playlists);
            playlistIds.forEach(pid => {
                const count = Array.isArray(window.__yocsPanel.playlists[pid]) ? window.__yocsPanel.playlists[pid].length : 0;
                html += `<li onclick="window.__yocsPanel.selectPlaylist('${pid}','${this._escapeHtml(typeof window.__yocsPanel.playlists[pid] === 'string' ? window.__yocsPanel.playlists[pid] : (window.__yocsPanel.playlists[pid]?.name || pid))}')" style="cursor:pointer;display:flex;align-items:center;padding:10px 8px;">📋 ${this._escapeHtml(typeof window.__yocsPanel.playlists[pid] === 'string' ? window.__yocsPanel.playlists[pid] : (window.__yocsPanel.playlists[pid]?.name || pid))} (${count})</li>`;
            });
        }
        
        html += '</ul>';
        modalInner.innerHTML = html;
        modalInner.parentElement.classList.remove('hidden');
    }

    selectPlaylist(pid, name) {
        window.__yocsPanel.selectedPlaylistId = pid;
    }

    showSettingsView() {
        if (this._settingsForm) {
            this._settingsForm.innerHTML = `
                <div class="setting-group">
                    <label style="display:block;font-weight:bold;margin-bottom:10px;">🔑 YouTube API 키</label>
                    <input type="password" id="api-key-input" class="input-field" placeholder="YouTube Data API v3 키를 입력하세요"/>
                </div>`;

            const saveBtn = document.getElementById('settings-save');
            if (!saveBtn) {
                this._settingsForm.insertAdjacentHTML('beforeend', '<button id="settings-save" class="input-field" style="text-align:center;background:#3ea6ff;color:#fff;font-weight:bold;margin-top:12px;">💾 저장</button>');
            }

            const saveBtnEl = document.getElementById('settings-save');
            if (saveBtnEl) {
                saveBtnEl.onclick = () => {
                    const apiKey = document.getElementById('api-key-input').value;
                    localStorage.setItem('yocs_api_key', apiKey);
                    // In real implementation, would update HA config via API
                    this.showToast('API 키가 설정되었습니다', 'success');
                };

                const savedApi = localStorage.getItem('yocs_api_key');
                if (savedApi) {
                    document.getElementById('api-key-input').value = savedApi;
                }
            }
        }
    }

    showToast(msg, type) {
        if (!this._toastContainer) return;
        
        const el = document.createElement('div');
        el.className = `toast-msg ${type || 'success'}`;
        el.textContent = msg;
        this._toastContainer.appendChild(el);
        setTimeout(() => { if (el.parentNode) el.remove(); }, 3000);
    }

    _escapeHtml(s) {
        if (!s) return '';
        const e = document.createElement('div');
        e.textContent = s;
        return e.innerHTML;
    }
}

// Register custom element
customElements.define('youtube-content-search-panel', YouTubeContentSearchPanel);
