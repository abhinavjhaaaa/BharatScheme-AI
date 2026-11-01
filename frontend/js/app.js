/**
 * BharatScheme AI — Frontend Application Logic
 * Clean, lightweight vanilla JS communicating with FastAPI backend
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    schemes: [],
    selectedForCompare: new Set(),
    activeCategory: '',
    searchQuery: '',
    currentSchemeDetail: null,
    isSubmittingChat: false,
    chatHistory: [],
  };

  // DOM Elements
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const schemesGrid = document.getElementById('schemes-grid');
  const resultsCount = document.getElementById('results-count');
  const searchInput = document.getElementById('scheme-search-input');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const categoryChips = document.querySelectorAll('.category-chip');
  const quickCompareBtn = document.getElementById('quick-compare-btn');
  const compareCountSpan = document.getElementById('compare-count');

  // Modal Elements
  const schemeModal = document.getElementById('scheme-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalTabs = document.querySelectorAll('.modal-tab');
  const modalPanes = document.querySelectorAll('.modal-pane');
  const modalTitle = document.getElementById('modal-title');
  const modalCategory = document.getElementById('modal-category');
  const modalMinistry = document.getElementById('modal-ministry');
  const modalFinancialAmount = document.getElementById('modal-financial-amount');
  const modalDescription = document.getElementById('modal-description');
  const modalBenefitsList = document.getElementById('modal-benefits-list');
  const modalEligibilitySummary = document.getElementById('modal-eligibility-summary');
  const modalExclusionsList = document.getElementById('modal-exclusions-list');
  const modalDocumentsList = document.getElementById('modal-documents-list');
  const modalHowToApply = document.getElementById('modal-how-to-apply');
  const modalHelpline = document.getElementById('modal-helpline');
  const modalOfficialLink = document.getElementById('modal-official-link');
  const modalAskAiBtn = document.getElementById('modal-ask-ai-btn');

  // Chat Elements
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  const chatSchemeFilter = document.getElementById('chat-scheme-filter');
  const promptChips = document.querySelectorAll('.prompt-chip');

  // Eligibility Elements
  const eligibilityForm = document.getElementById('eligibility-form');
  const eligOccupation = document.getElementById('elig-occupation');
  const sectionFarmerFields = document.getElementById('section-farmer-fields');
  const sectionStudentFields = document.getElementById('section-student-fields');
  const eligibilityResultsPanel = document.getElementById('eligibility-results-panel');
  const resetEligBtn = document.getElementById('reset-elig-btn');

  // Compare Elements
  const compareSelectorList = document.getElementById('compare-selector-list');
  const executeCompareBtn = document.getElementById('execute-compare-btn');
  const comparisonResultsWrap = document.getElementById('comparison-results-wrap');

  // Status Indicator
  const systemStatusIndicator = document.getElementById('system-status-indicator');
  const systemStatusText = document.getElementById('system-status-text');

  // =========================================================================
  // Initialization
  // =========================================================================
  initApp();

  async function initApp() {
    setupTabNavigation();
    setupSearchAndFilter();
    setupModalEvents();
    setupChatEvents();
    setupEligibilityEvents();
    setupCompareEvents();
    await checkSystemHealth();
    await loadSchemes();
  }

  // =========================================================================
  // System Health
  // =========================================================================
  async function checkSystemHealth() {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'healthy') {
          systemStatusIndicator.style.backgroundColor = 'var(--green)';
          systemStatusText.textContent = `Ollama (${data.ollama_model}) Active`;
        } else {
          systemStatusIndicator.style.backgroundColor = 'var(--saffron)';
          systemStatusText.textContent = 'Degraded (Indices checking)';
        }
      }
    } catch (err) {
      systemStatusIndicator.style.backgroundColor = '#DC2626';
      systemStatusText.textContent = 'API Offline';
    }
  }

  // =========================================================================
  // Tab Navigation
  // =========================================================================
  function setupTabNavigation() {
    navTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetTab = tab.getAttribute('data-tab');
        switchTab(targetTab);
      });
    });

    // Also enable clicking the 4 homepage feature cards
    document.querySelectorAll('.feature-card[data-tab]').forEach(card => {
      card.addEventListener('click', () => {
        const targetTab = card.getAttribute('data-tab');
        if (targetTab) switchTab(targetTab);
      });
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const targetTab = card.getAttribute('data-tab');
          if (targetTab) switchTab(targetTab);
        }
      });
    });
  }

  function switchTab(targetTabName) {
    navTabs.forEach(t => {
      if (t.getAttribute('data-tab') === targetTabName) {
        t.classList.add('active');
        t.setAttribute('aria-selected', 'true');
      } else {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      }
    });

    document.querySelectorAll('.feature-card[data-tab]').forEach(card => {
      if (card.getAttribute('data-tab') === targetTabName) {
        card.classList.add('active-feature');
      } else {
        card.classList.remove('active-feature');
      }
    });

    tabPanes.forEach(pane => {
      if (pane.id === `tab-${targetTabName}`) {
        pane.classList.add('active');
      } else {
        pane.classList.remove('active');
      }
    });

    // Special handlers when opening specific tabs
    if (targetTabName === 'compare') {
      populateCompareSelector();
      if (state.selectedForCompare.size >= 2) {
        runComparison(Array.from(state.selectedForCompare));
      }
    }
  }

  // =========================================================================
  // Scheme Explorer & Data Fetching
  // =========================================================================
  async function loadSchemes() {
    try {
      resultsCount.textContent = 'Loading verified schemes...';
      const params = new URLSearchParams();
      if (state.activeCategory) params.append('category', state.activeCategory);
      if (state.searchQuery) params.append('q', state.searchQuery);

      const url = `/api/schemes?${params.toString()}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to load schemes.');

      const data = await res.json();
      state.schemes = data.schemes || [];
      renderSchemesGrid(state.schemes);
      populateCompareSelector();
    } catch (err) {
      resultsCount.textContent = 'Error loading schemes.';
      schemesGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <p>⚠️ Could not connect to API server. Please make sure the FastAPI backend is running.</p>
        </div>
      `;
    }
  }

  function renderSchemesGrid(schemes) {
    resultsCount.textContent = `Showing ${schemes.length} verified government scheme${schemes.length === 1 ? '' : 's'}`;

    if (!schemes || schemes.length === 0) {
      schemesGrid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-icon">🔍</div>
          <h3>No matching schemes found</h3>
          <p>Try clearing your search keyword or switching category filter.</p>
        </div>
      `;
      return;
    }

    schemesGrid.innerHTML = schemes.map(scheme => {
      const isSelected = state.selectedForCompare.has(scheme.scheme_id);
      const catClass = (scheme.category || 'general').toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '') || 'general';

      return `
        <article class="scheme-card" data-scheme-id="${scheme.scheme_id}">
          <div>
            <div class="card-top">
              <span class="category-badge ${catClass}">${escapeHtml(scheme.category || 'General')}</span>
              <label class="card-compare-check" title="Select to compare">
                <input type="checkbox" class="compare-checkbox" data-id="${scheme.scheme_id}" ${isSelected ? 'checked' : ''}>
                Compare
              </label>
            </div>

            <h3 class="scheme-title">${escapeHtml(scheme.scheme_name)}</h3>
            <div class="scheme-ministry">🏛️ ${escapeHtml(scheme.ministry || '')}</div>

            <div class="financial-pill">
              💰 ${escapeHtml(scheme.financial_assistance || 'Financial support available')}
            </div>

            <p class="scheme-desc-preview">
              ${escapeHtml(scheme.description || '')}
            </p>
          </div>

          <div class="card-actions">
            <button class="btn btn-primary btn-sm view-details-btn" data-id="${scheme.scheme_id}">
              View Full Details
            </button>
            <button class="btn btn-outline btn-sm ask-ai-card-btn" data-id="${scheme.scheme_id}">
              Ask AI
            </button>
          </div>
        </article>
      `;
    }).join('');

    // Attach card event listeners
    schemesGrid.querySelectorAll('.view-details-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.getAttribute('data-id');
        openSchemeModal(id);
      });
    });

    schemesGrid.querySelectorAll('.ask-ai-card-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.getAttribute('data-id');
        startNewChat(id, `What are the benefits, amounts, and eligibility requirements for ${id}?`, false);
      });
    });

    schemesGrid.querySelectorAll('.compare-checkbox').forEach(cb => {
      cb.addEventListener('change', (e) => {
        const id = e.target.getAttribute('data-id');
        if (e.target.checked) {
          if (state.selectedForCompare.size >= 3) {
            alert('You can compare a maximum of 3 schemes at a time.');
            e.target.checked = false;
            return;
          }
          state.selectedForCompare.add(id);
        } else {
          state.selectedForCompare.delete(id);
        }
        updateCompareButton();
      });
    });
  }

  function updateCompareButton() {
    const count = state.selectedForCompare.size;
    compareCountSpan.textContent = count;
    quickCompareBtn.disabled = count < 2;
  }

  // =========================================================================
  // Search & Filter Setup
  // =========================================================================
  function setupSearchAndFilter() {
    let debounceTimer = null;
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.trim();
      clearSearchBtn.style.display = state.searchQuery ? 'block' : 'none';

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadSchemes();
      }, 300);
    });

    clearSearchBtn.addEventListener('click', () => {
      searchInput.value = '';
      state.searchQuery = '';
      clearSearchBtn.style.display = 'none';
      loadSchemes();
      searchInput.focus();
    });

    categoryChips.forEach(chip => {
      chip.addEventListener('click', () => {
        categoryChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        state.activeCategory = chip.getAttribute('data-category');
        loadSchemes();
      });
    });

    quickCompareBtn.addEventListener('click', () => {
      if (state.selectedForCompare.size >= 2) {
        switchTab('compare');
      }
    });
  }

  // =========================================================================
  // Modal Details
  // =========================================================================
  function setupModalEvents() {
    modalCloseBtn.addEventListener('click', closeSchemeModal);
    schemeModal.addEventListener('click', (e) => {
      if (e.target === schemeModal) closeSchemeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && schemeModal.style.display !== 'none') {
        closeSchemeModal();
      }
    });

    modalTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-modaltab');
        modalTabs.forEach(t => t.classList.remove('active'));
        modalPanes.forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`modal-pane-${target}`).classList.add('active');
      });
    });

    modalAskAiBtn.addEventListener('click', () => {
      if (!state.currentSchemeDetail) return;
      const id = state.currentSchemeDetail.scheme_id;
      const name = state.currentSchemeDetail.scheme_name || id;
      closeSchemeModal();
      startNewChat(id, `Explain the application process and requirements for ${id}.`, false);
    });
  }

  async function openSchemeModal(schemeId) {
    try {
      const res = await fetch(`/api/schemes/${schemeId}`);
      if (!res.ok) throw new Error('Scheme details not found.');
      const scheme = await res.json();
      state.currentSchemeDetail = scheme;

      modalTitle.textContent = scheme.scheme_name;
      modalCategory.textContent = scheme.category || 'General';
      modalMinistry.textContent = `🏛️ ${scheme.ministry || 'Government of India'}`;
      modalFinancialAmount.textContent = scheme.financial_assistance || 'N/A';
      modalDescription.textContent = scheme.description || 'No description provided.';

      modalBenefitsList.innerHTML = (scheme.benefits || []).map(b => `<li>${escapeHtml(b)}</li>`).join('');
      modalEligibilitySummary.textContent = scheme.eligibility_summary || 'Please refer to official guidelines.';

      modalExclusionsList.innerHTML = (scheme.exclusions || []).map(ex => `<li>${escapeHtml(ex)}</li>`).join('');
      modalDocumentsList.innerHTML = (scheme.documents_required || []).map(doc => `<li>${escapeHtml(doc)}</li>`).join('');

      modalHowToApply.textContent = scheme.how_to_apply || 'Apply online via the official government portal.';
      modalHelpline.textContent = scheme.helpline || 'Not available';

      if (scheme.official_url) {
        modalOfficialLink.href = scheme.official_url;
        modalOfficialLink.style.display = 'inline-flex';
      } else {
        modalOfficialLink.style.display = 'none';
      }

      // Reset to first tab
      modalTabs[0].click();
      schemeModal.style.display = 'flex';
    } catch (err) {
      alert(`Could not load details: ${err.message}`);
    }
  }

  function closeSchemeModal() {
    schemeModal.style.display = 'none';
    state.currentSchemeDetail = null;
  }

  const HINGLISH_KEYWORDS = new Set([
    "kya", "kaise", "kitna", "kitne", "kitni", "kab", "kahan", "kaun",
    "kisko", "kise", "kinhe", "mujhe", "mera", "meri", "mere", "chahiye",
    "milega", "milta", "milte", "milenge", "paane", "prapt", "yojana",
    "yojna", "labh", "fayda", "fayde", "aavedan", "patra", "patrata",
    "yogyata", "kyu", "kyon", "liye", "batao", "bataiye", "samjhao",
    "paisa", "paise", "rupaye", "rupee", "kisan", "kisano", "chhatravritti",
    "padhai", "dastavez", "kagaz", "shiksha", "sahayata", "kare", "karna",
    "sakta", "sakti", "sakte", "hai", "hain", "bhi", "nahi", "nahin",
    "hoga", "hogi", "honge", "bhare", "bharo", "jankari",
    "kisme", "isme", "usme", "ghar", "awas", "bima", "pension"
  ]);

  function detectClientLanguage(text) {
    if (!text) return 'en';
    if (/[\u0900-\u097F]/.test(text)) return 'hi';
    const tokens = text.toLowerCase().match(/[a-z]+/g) || [];
    if (tokens.some(t => HINGLISH_KEYWORDS.has(t))) {
      return 'hinglish';
    }
    return 'en';
  }

  // =========================================================================
  // AI Assistant (RAG Chat)
  // =========================================================================
  function setupChatEvents() {
    // Reusable function to attach prompt chip clicks
    attachPromptChipListeners();

    // New Chat Button
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => {
        startNewChat(null, '', false);
      });
    }

    // Clear Scheme Focus Button
    const clearFocusBtn = document.getElementById('clear-scheme-focus-btn');
    if (clearFocusBtn) {
      clearFocusBtn.addEventListener('click', () => {
        startNewChat(null, '', false);
      });
    }

    // Filter Dropdown Change
    if (chatSchemeFilter) {
      chatSchemeFilter.addEventListener('change', (e) => {
        const selectedId = e.target.value;
        startNewChat(selectedId, selectedId ? `What are the benefits, amounts, and eligibility requirements for ${selectedId}?` : '', false);
      });
    }

    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });

    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = chatInput.value.trim();
      if (!question || state.isSubmittingChat) return;

      const schemeFilter = chatSchemeFilter.value || null;
      const inputLang = detectClientLanguage(question);

      // Append user message
      appendChatMessage('user', question);
      state.chatHistory.push({ role: 'user', content: question });
      chatInput.value = '';
      state.isSubmittingChat = true;

      // Append loading assistant bubble in user's language
      const loadingMsgId = appendChatLoadingMessage(inputLang);

      try {
        const payload = {
          question: question,
          scheme_id: schemeFilter,
          top_k: 5,
          history: state.chatHistory.slice(-6)
        };

        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Server error ${res.status}`);
        }

        const data = await res.json();
        removeChatLoadingMessage(loadingMsgId);
        state.chatHistory.push({ role: 'assistant', content: data.answer });
        appendChatMessage('assistant', data.answer, data.sources, data.confidence, data.is_grounded, data.detected_language || inputLang);
      } catch (err) {
        removeChatLoadingMessage(loadingMsgId);
        let errorMsg = `⚠️ Unable to complete request: ${err.message}. Please verify local Ollama service is running.`;
        if (inputLang === 'hi') {
          errorMsg = `⚠️ अनुरोध पूरा करने में समस्या: ${err.message}। कृपया जांचें कि Ollama सर्विस चालू है।`;
        } else if (inputLang === 'hinglish') {
          errorMsg = `⚠️ Request poori nahi ho payi: ${err.message}. Kripya verify karein ki local Ollama chal raha hai.`;
        }
        appendChatMessage(
          'assistant',
          errorMsg,
          [],
          'low',
          false,
          inputLang
        );
      } finally {
        state.isSubmittingChat = false;
        chatInput.focus();
      }
    });
  }

  function attachPromptChipListeners() {
    const chips = document.querySelectorAll('.prompt-chip');
    chips.forEach(chip => {
      chip.onclick = () => {
        const query = chip.getAttribute('data-query');
        chatInput.value = query;
        chatForm.dispatchEvent(new Event('submit'));
      };
    });
  }

  function startNewChat(schemeId = null, initialQuery = '', autoSubmit = false) {
    switchTab('chat');

    const cleanSchemeId = (schemeId && String(schemeId).trim()) ? String(schemeId).trim() : null;
    state.currentChatScheme = cleanSchemeId;
    state.chatHistory = []; // Reset conversation history

    if (chatSchemeFilter) {
      chatSchemeFilter.value = cleanSchemeId || '';
    }

    const sessionBadge = document.getElementById('chat-session-badge');
    const sessionTitle = document.getElementById('chat-session-title');
    const clearFocusBtn = document.getElementById('clear-scheme-focus-btn');

    chatMessages.innerHTML = ''; // Fresh clean chat container

    if (cleanSchemeId) {
      const schemeObj = state.schemes.find(s => s.scheme_id === cleanSchemeId);
      const schemeName = schemeObj ? schemeObj.scheme_name : cleanSchemeId;

      if (sessionTitle) sessionTitle.textContent = `Focus: ${cleanSchemeId}`;
      if (sessionBadge) sessionBadge.classList.add('scheme-focused');
      if (clearFocusBtn) clearFocusBtn.style.display = 'inline-block';

      // Scheme-dedicated welcome message
      const welcomeDiv = document.createElement('div');
      welcomeDiv.className = 'chat-message assistant';
      welcomeDiv.innerHTML = `
        <div class="message-avatar assistant-avatar">
          <img src="/static/assets/india_flag.png" alt="India Flag" class="avatar-flag-icon">
        </div>
        <div class="message-content">
          <div class="session-welcome-header">
            <span class="focused-scheme-tag">🎯 Scheme Focus: <strong>${escapeHtml(cleanSchemeId)}</strong></span>
          </div>
          <p>Namaste! You have opened a new dedicated chat for <strong>${escapeHtml(schemeName)}</strong>.</p>
          <p style="margin-top: 6px; font-size: 0.84rem; color: var(--text-muted);">
            Ask me anything about eligibility criteria, financial assistance amounts, required documents, or application guidelines for this scheme.
          </p>
          <p style="margin-top: 6px; font-size: 0.8rem; color: var(--text-sub);">
            🇮🇳 <em>आप इस योजना के बारे में हिन्दी या Hinglish में भी पूछ सकते हैं (जैसे: 'इसमें कितना पैसा मिलता है?', 'पात्रता क्या है?')</em>
          </p>
        </div>
      `;
      chatMessages.appendChild(welcomeDiv);
    } else {
      if (sessionTitle) sessionTitle.textContent = 'All Schemes';
      if (sessionBadge) sessionBadge.classList.remove('scheme-focused');
      if (clearFocusBtn) clearFocusBtn.style.display = 'none';

      // General schemes welcome message
      const welcomeDiv = document.createElement('div');
      welcomeDiv.className = 'chat-message assistant';
      welcomeDiv.innerHTML = `
        <div class="message-avatar assistant-avatar">
          <img src="/static/assets/india_flag.png" alt="India Flag" class="avatar-flag-icon">
        </div>
        <div class="message-content">
          <p>Namaste! I am <strong><span class="brand-bharat">भारत</span><span class="brand-scheme">Scheme</span> AI</strong>. Ask me anything about Indian government schemes, eligibility rules, financial assistance amounts, or required documents.</p>
          <p class="citation-hint">Every answer is strictly grounded in official documents with verified page citations.</p>
        </div>
      `;
      chatMessages.appendChild(welcomeDiv);
    }

    // Update suggested prompt chips for this scheme or general
    updateSuggestedPrompts(cleanSchemeId);

    chatInput.value = initialQuery || '';
    chatInput.focus();

    if (autoSubmit && initialQuery) {
      chatForm.dispatchEvent(new Event('submit'));
    }
  }

  function updateSuggestedPrompts(schemeId) {
    const suggestedBox = document.querySelector('.suggested-queries');
    if (!suggestedBox) return;

    if (!schemeId) {
      suggestedBox.innerHTML = `
        <h4>💡 Recommended Questions</h4>
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-sub); margin-bottom: 4px;">🇬🇧 English</div>
        <button class="prompt-chip" data-query="How much financial assistance does PM-KISAN provide and in how many installments?">
          "How much financial assistance does PM-KISAN provide?"
        </button>
        <button class="prompt-chip" data-query="What is the family income limit for PM-USP Central Sector Scholarship Scheme?">
          "What is the income limit for PM-USP scholarship?"
        </button>

        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-sub); margin-top: 10px; margin-bottom: 4px;">🇮🇳 Hinglish</div>
        <button class="prompt-chip" data-query="PM kisan me kitna paisa milta hai aur kist kab aati hai?">
          "PM kisan me kitna paisa milta hai?"
        </button>
        <button class="prompt-chip" data-query="Scholarship ke liye kya eligibility aur income limit hai?">
          "Scholarship ke liye kya eligibility aur income limit hai?"
        </button>

        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-sub); margin-top: 10px; margin-bottom: 4px;">🇮🇳 हिन्दी (Hindi)</div>
        <button class="prompt-chip" data-query="पीएम किसान योजना में कितने पैसे और किस्तें मिलती हैं?">
          "पीएम किसान योजना में कितने पैसे मिलते हैं?"
        </button>
        <button class="prompt-chip" data-query="स्कॉलरशिप योजना के लिए क्या पात्रता, नियम और शर्तें हैं?">
          "स्कॉलरशिप योजना के लिए क्या पात्रता और नियम हैं?"
        </button>
      `;
    } else {
      suggestedBox.innerHTML = `
        <h4>💡 Quick Questions for ${escapeHtml(schemeId)}</h4>
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-sub); margin-bottom: 4px;">🇬🇧 English</div>
        <button class="prompt-chip" data-query="What are the financial assistance benefits and amounts for ${schemeId}?">
          "What are the benefits and amounts for ${schemeId}?"
        </button>
        <button class="prompt-chip" data-query="What are the complete eligibility criteria and rules for ${schemeId}?">
          "What are the eligibility criteria for ${schemeId}?"
        </button>

        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-sub); margin-top: 10px; margin-bottom: 4px;">🇮🇳 Hinglish</div>
        <button class="prompt-chip" data-query="${schemeId} me kitna paisa milta hai aur kaun eligible hai?">
          "${schemeId} me kitna paisa milta hai aur kaun eligible hai?"
        </button>
        <button class="prompt-chip" data-query="${schemeId} ke liye aavedan kaise karein aur kya documents lagenge?">
          "${schemeId} me aavedan kaise karein aur kya kagaz chahiye?"
        </button>

        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-sub); margin-top: 10px; margin-bottom: 4px;">🇮🇳 हिन्दी (Hindi)</div>
        <button class="prompt-chip" data-query="${schemeId} योजना में क्या लाभ और वित्तीय सहायता मिलती है?">
          "${schemeId} योजना में क्या लाभ और वित्तीय सहायता मिलती है?"
        </button>
        <button class="prompt-chip" data-query="${schemeId} योजना के लिए आवश्यक दस्तावेज और पात्रता नियम क्या हैं?">
          "${schemeId} के लिए आवश्यक दस्तावेज और पात्रता नियम क्या हैं?"
        </button>
      `;
    }

    attachPromptChipListeners();
  }

  function appendChatMessage(role, text, sources = [], confidence = '', isGrounded = true, detectedLanguage = 'en') {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${role}`;

    const avatarHtml = role === 'assistant'
      ? `<img src="/static/assets/india_flag.png" alt="India Flag" class="avatar-flag-icon">`
      : '👤';

    let langBadgeHtml = '';
    if (role === 'assistant' && detectedLanguage) {
      if (detectedLanguage === 'hi') {
        langBadgeHtml = '<span class="lang-badge lang-hi" title="Answered in Hindi">🇮🇳 हिन्दी</span>';
      } else if (detectedLanguage === 'hinglish') {
        langBadgeHtml = '<span class="lang-badge lang-hinglish" title="Answered in Hinglish">🇮🇳 Hinglish</span>';
      } else {
        langBadgeHtml = '<span class="lang-badge lang-en" title="Answered in English">🇬🇧 English</span>';
      }
    }

    let citationsHtml = '';
    if (sources && sources.length > 0) {
      const sourceBadges = sources.map((s, idx) => `
        <div class="citation-badge" title="Click to view excerpt" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
          📄 ${escapeHtml(s.source_file)} (Page ${s.page_number})
          <span style="opacity: 0.7; font-size: 0.7rem;">[${Math.round(s.similarity_score * 100)}%]</span>
        </div>
        <div class="citation-details" style="display: none;">
          <strong>Source:</strong> ${escapeHtml(s.source_file)} | <strong>Page:</strong> ${s.page_number} | <strong>Relevance:</strong> ${s.similarity_score}<br>
          <em style="color: var(--text-muted); display: block; margin-top: 4px;">"${escapeHtml(s.snippet)}"</em>
        </div>
      `).join('');

      citationsHtml = `
        <div class="citations-container">
          <div class="citations-title">
            <span>Verified Official Citations:</span>
            ${confidence ? `<span class="confidence-chip ${confidence}">${confidence.toUpperCase()} CONFIDENCE</span>` : ''}
          </div>
          ${sourceBadges}
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="message-avatar ${role === 'assistant' ? 'assistant-avatar' : ''}">${avatarHtml}</div>
      <div class="message-content">
        ${langBadgeHtml ? `<div class="message-meta-header">${langBadgeHtml}</div>` : ''}
        <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
        ${citationsHtml}
      </div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendChatLoadingMessage(lang = 'en') {
    const id = `loading-${Date.now()}`;
    const msgDiv = document.createElement('div');
    msgDiv.id = id;
    msgDiv.className = 'chat-message assistant';

    let loadingText = 'Searching official government documents & generating grounded response...';
    if (lang === 'hi') {
      loadingText = 'आधिकारिक सरकारी दस्तावेजों में खोज जारी है और सत्यापित उत्तर तैयार किया जा रहा है...';
    } else if (lang === 'hinglish') {
      loadingText = 'Official government documents me search ho raha hai aur verified response generate ho raha hai...';
    }

    msgDiv.innerHTML = `
      <div class="message-avatar assistant-avatar">
        <img src="/static/assets/india_flag.png" alt="India Flag" class="avatar-flag-icon">
      </div>
      <div class="message-content">
        <p style="color: var(--text-muted); display: flex; align-items: center; gap: 8px;">
          <span class="loading-spinner"></span>
          <em>${escapeHtml(loadingText)}</em>
        </p>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
  }

  function removeChatLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  // =========================================================================
  // Eligibility Checker
  // =========================================================================
  function setupEligibilityEvents() {
    eligOccupation.addEventListener('change', (e) => {
      const val = e.target.value;
      sectionFarmerFields.style.display = val === 'farmer' ? 'block' : 'none';
      sectionStudentFields.style.display = val === 'student' ? 'block' : 'none';
    });

    resetEligBtn.addEventListener('click', () => {
      eligibilityForm.reset();
      sectionFarmerFields.style.display = 'none';
      sectionStudentFields.style.display = 'none';
      eligibilityResultsPanel.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>Ready to Check Eligibility</h3>
          <p>Complete your profile details on the left and click "Evaluate My Eligibility" to see transparent rule matching results.</p>
        </div>
      `;
    });

    eligibilityForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const occupation = eligOccupation.value;
      const income = parseFloat(document.getElementById('elig-income').value);
      const ageVal = document.getElementById('elig-age').value;
      const age = ageVal ? parseInt(ageVal, 10) : null;
      const schemeId = document.getElementById('elig-scheme-select').value || null;

      const profile = {
        occupation: occupation,
        annual_income: income,
        age: age,
        scheme_id: schemeId,
      };

      // General fields for the 10 added schemes (sent only if the element exists)
      const genderEl = document.getElementById('elig-gender');
      if (genderEl && genderEl.value) profile.gender = genderEl.value;
      const boolField = (id, key) => {
        const el = document.getElementById(id);
        if (el) profile[key] = el.checked;
      };
      boolField('elig-bank-account', 'has_bank_account');
      boolField('elig-lpg', 'has_lpg_connection');
      boolField('elig-houseless', 'is_houseless_or_kutcha_house');
      boolField('elig-secc', 'is_secc_deprived');
      boolField('elig-artisan', 'is_traditional_artisan');
      boolField('elig-business-plan', 'has_business_plan');

      if (occupation === 'farmer') {
        profile.is_landholding_farmer = document.getElementById('elig-landholding').checked;
        profile.is_income_tax_payer = document.getElementById('elig-taxpayer').checked;
        profile.is_government_employee = document.getElementById('elig-gov-emp').checked;
        profile.is_institutional_landholder = document.getElementById('elig-inst-land').checked;
      } else if (occupation === 'student') {
        profile.is_student = true;
        profile.education_level = document.getElementById('elig-education-level').value;
        const perc = document.getElementById('elig-percentile').value;
        if (perc) profile.class_12_percentile = parseFloat(perc);
        profile.special_category = document.getElementById('elig-special-cat').value;
        profile.is_aicte_approved_institution = document.getElementById('elig-aicte').checked;
        profile.is_regular_course = document.getElementById('elig-regular').checked;
        profile.is_technical_degree_or_diploma = profile.education_level === 'undergraduate' || profile.education_level === 'diploma';
      }

      eligibilityResultsPanel.innerHTML = `
        <div class="empty-state">
          <p>Evaluating profile against official government eligibility criteria...</p>
        </div>
      `;

      try {
        const res = await fetch('/api/eligibility', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(profile)
        });

        if (!res.ok) throw new Error('Evaluation failed.');
        const data = await res.json();
        renderEligibilityResults(data.results);
      } catch (err) {
        eligibilityResultsPanel.innerHTML = `
          <div class="empty-state">
            <p>⚠️ Error evaluating eligibility: ${err.message}</p>
          </div>
        `;
      }
    });
  }

  function renderEligibilityResults(results) {
    if (!results || results.length === 0) {
      eligibilityResultsPanel.innerHTML = `
        <div class="empty-state">
          <p>No schemes evaluated.</p>
        </div>
      `;
      return;
    }

    eligibilityResultsPanel.innerHTML = results.map(r => {
      const statusClass = r.status; // eligible, ineligible, potentially_eligible

      const matchedList = (r.matched_criteria || []).length > 0
        ? `<ul class="styled-list check-list">${r.matched_criteria.map(m => `<li>${escapeHtml(m)}</li>`).join('')}</ul>`
        : '<p style="font-size: 0.8rem; color: var(--text-sub);">No criteria confirmed.</p>';

      const failedList = (r.failed_criteria || []).length > 0
        ? `<div style="margin-top: 8px;">
            <strong style="font-size: 0.8rem; color: #DC2626;">Unmet Requirements:</strong>
            <ul class="styled-list cross-list">${r.failed_criteria.map(f => `<li>${escapeHtml(f)}</li>`).join('')}</ul>
           </div>`
        : '';

      const missingList = (r.missing_info || []).length > 0
        ? `<div style="margin-top: 8px;">
            <strong style="font-size: 0.8rem; color: var(--saffron);">Requires Verification:</strong>
            <ul class="styled-list">${r.missing_info.map(mi => `<li>${escapeHtml(mi)}</li>`).join('')}</ul>
           </div>`
        : '';

      return `
        <div class="eligibility-card ${statusClass}">
          <span class="status-badge ${statusClass}">${escapeHtml(r.verdict)}</span>
          <h4 style="font-size: 1.05rem; font-weight: 700;">${escapeHtml(r.scheme_name)}</h4>
          <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 8px;">${escapeHtml(r.category)} • ${escapeHtml(r.ministry)}</p>

          <div style="background: var(--bg-app); padding: 8px 12px; border-radius: 4px; font-size: 0.82rem; margin-bottom: 10px;">
            <strong>Benefit:</strong> ${escapeHtml(r.financial_assistance)}
          </div>

          <div>
            <strong style="font-size: 0.8rem; color: var(--green);">Matched Criteria:</strong>
            ${matchedList}
          </div>

          ${failedList}
          ${missingList}

          <div style="margin-top: 14px; display: flex; gap: 8px;">
            ${r.official_url ? `<a href="${r.official_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">Official Portal</a>` : ''}
            <button class="btn btn-outline btn-sm ask-ai-elig-btn" data-id="${escapeHtml(r.scheme_id)}">Ask AI Questions</button>
          </div>
        </div>
      `;
    }).join('');

    eligibilityResultsPanel.querySelectorAll('.ask-ai-elig-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.getAttribute('data-id');
        startNewChat(id, `What are the required documents and application steps for ${id}?`, false);
      });
    });
  }

  // =========================================================================
  // Scheme Comparison
  // =========================================================================
  function setupCompareEvents() {
    executeCompareBtn.addEventListener('click', () => {
      const checkedBoxes = compareSelectorList.querySelectorAll('input:checked');
      const selected = Array.from(checkedBoxes).map(cb => cb.value);

      if (selected.length < 2) {
        alert('Please select at least 2 schemes to compare.');
        return;
      }
      if (selected.length > 4) {
        alert('You can compare a maximum of 4 schemes at once.');
        return;
      }

      runComparison(selected);
    });
  }

  function populateCompareSelector() {
    if (!state.schemes || state.schemes.length === 0) return;

    compareSelectorList.innerHTML = state.schemes.map(s => {
      const isChecked = state.selectedForCompare.has(s.scheme_id);
      return `
        <label class="checkbox-group" style="font-weight: 600;">
          <input type="checkbox" value="${s.scheme_id}" class="form-checkbox" ${isChecked ? 'checked' : ''}>
          ${escapeHtml(s.scheme_id)} (${escapeHtml(s.category)})
        </label>
      `;
    }).join('');
  }

  async function runComparison(schemeIds) {
    comparisonResultsWrap.innerHTML = `
      <div class="empty-state">
        <p>Generating side-by-side comparison matrix...</p>
      </div>
    `;

    try {
      const res = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheme_ids: schemeIds })
      });

      if (!res.ok) throw new Error('Failed to retrieve comparison.');
      const data = await res.json();
      renderComparisonTable(data);
    } catch (err) {
      comparisonResultsWrap.innerHTML = `
        <div class="empty-state">
          <p>⚠️ Error comparing schemes: ${err.message}</p>
        </div>
      `;
    }
  }

  function renderComparisonTable(data) {
    const schemes = data.schemes;
    const matrix = data.comparison_matrix;

    const headers = schemes.map(s => `
      <th>
        <div style="font-size: 1rem; font-weight: 700; color: var(--primary);">${escapeHtml(s.scheme_name)}</div>
        <div style="font-size: 0.75rem; color: var(--text-sub);">${escapeHtml(s.scheme_id)}</div>
      </th>
    `).join('');

    const rows = matrix.map(row => {
      const cells = schemes.map(s => {
        const val = row.values[s.scheme_id] || 'N/A';
        return `<td>${escapeHtml(String(val))}</td>`;
      }).join('');

      return `
        <tr>
          <th>${escapeHtml(row.attribute)}</th>
          ${cells}
        </tr>
      `;
    }).join('');

    comparisonResultsWrap.innerHTML = `
      <div class="comparison-table-wrap">
        <table class="comparison-table">
          <thead>
            <tr>
              <th>Comparison Feature</th>
              ${headers}
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
  }

  // =========================================================================
  // Utilities
  // =========================================================================
  function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
