/**
 * TestEventTracker - Système de journalisation détaillée des événements de test
 * 
 * Ce script enregistre tous les événements importants pendant un test :
 * - Début/fin de test
 * - Visualisation et réponses aux questions
 * - Changements de focus (page, onglet)
 * - Violations de sécurité
 * - Actions utilisateur (redimensionnement, etc.)
 */

class TestEventTracker {
    constructor(testId, sessionId = null) {
        this.testId = testId;
        this.sessionId = sessionId || this.generateSessionId();
        this.currentQuestion = 1;
        this.startTime = Date.now();
        this.lastFocusTime = Date.now();
        this.isTracking = false;
        this.eventQueue = [];
        this.maxQueueSize = 10;
        this.flushInterval = 5000; // 5 secondes
        
        // Configuration
        this.config = {
            trackFocus: true,
            trackResize: true,
            trackVisibility: true,
            trackKeyboard: true,
            trackMouse: true,
            trackNetwork: true,
            autoFlush: true
        };
        
        this.init();
    }
    
    /**
     * Initialise le tracker
     */
    init() {
        if (this.isTracking) return;
        
        console.log('🔍 Initialisation du TestEventTracker pour le test', this.testId);
        
        this.isTracking = true;
        this.setupEventListeners();
        this.startAutoFlush();
        
        // Enregistrer le début du test
        this.logEvent('test_start', {
            session_id: this.sessionId,
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            window_size: `${window.innerWidth}x${window.innerHeight}`
        });
    }
    
    /**
     * Configure tous les écouteurs d'événements
     */
    setupEventListeners() {
        // Événements de focus
        if (this.config.trackFocus) {
            document.addEventListener('focusin', () => this.handleFocusIn());
            document.addEventListener('focusout', () => this.handleFocusOut());
            window.addEventListener('focus', () => this.handleWindowFocus());
            window.addEventListener('blur', () => this.handleWindowBlur());
            document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
        }
        
        // Événements de redimensionnement
        if (this.config.trackResize) {
            window.addEventListener('resize', () => this.handleResize());
        }
        
        // Événements de clavier
        if (this.config.trackKeyboard) {
            document.addEventListener('keydown', (e) => this.handleKeyDown(e));
            document.addEventListener('keyup', (e) => this.handleKeyUp(e));
        }
        
        // Événements de souris
        if (this.config.trackMouse) {
            document.addEventListener('contextmenu', (e) => this.handleRightClick(e));
            document.addEventListener('copy', (e) => this.handleCopy(e));
            document.addEventListener('paste', (e) => this.handlePaste(e));
        }
        
        // Événements de réseau
        if (this.config.trackNetwork) {
            window.addEventListener('online', () => this.handleConnectionRestored());
            window.addEventListener('offline', () => this.handleConnectionLost());
        }
        
        // Événements de plein écran
        document.addEventListener('fullscreenchange', () => this.handleFullscreenChange());
        
        // Événements de soumission de formulaire
        document.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Événements de changement de question
        this.setupQuestionTracking();
        
        console.log('✅ Écouteurs d\'événements configurés');
    }
    
    /**
     * Configure le tracking des questions
     */
    setupQuestionTracking() {
        // Observer les changements dans le DOM pour détecter les changements de question
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    // Vérifier si c'est un changement de question
                    const questionElements = document.querySelectorAll('.question-container, .question, [data-question]');
                    if (questionElements.length > 0) {
                        const currentQuestionNumber = this.extractQuestionNumber(questionElements[0]);
                        if (currentQuestionNumber && currentQuestionNumber !== this.currentQuestion) {
                            this.currentQuestion = currentQuestionNumber;
                            this.logEvent('question_view', {
                                question_number: this.currentQuestion,
                                previous_question: this.currentQuestion - 1
                            });
                        }
                    }
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Extrait le numéro de question d'un élément
     */
    extractQuestionNumber(element) {
        // Essayer différentes méthodes pour extraire le numéro de question
        const dataQuestion = element.getAttribute('data-question');
        if (dataQuestion) return parseInt(dataQuestion);
        
        const questionText = element.textContent;
        const match = questionText.match(/question\s*(\d+)/i);
        if (match) return parseInt(match[1]);
        
        // Chercher dans les éléments enfants
        const questionNumberElement = element.querySelector('.question-number, .numero-question');
        if (questionNumberElement) {
            const text = questionNumberElement.textContent;
            const match = text.match(/(\d+)/);
            if (match) return parseInt(match[1]);
        }
        
        return null;
    }
    
    /**
     * Gère l'événement de focus sur la page
     */
    handleFocusIn() {
        const now = Date.now();
        const timeAway = now - this.lastFocusTime;
        
        if (timeAway > 1000) { // Plus d'1 seconde d'absence
            this.logEvent('page_focus', {
                time_away_ms: timeAway,
                element: document.activeElement?.tagName || 'unknown'
            });
        }
        
        this.lastFocusTime = now;
    }
    
    /**
     * Gère l'événement de perte de focus
     */
    handleFocusOut() {
        this.logEvent('page_blur', {
            element: document.activeElement?.tagName || 'unknown'
        });
    }
    
    /**
     * Gère le focus de la fenêtre
     */
    handleWindowFocus() {
        this.logEvent('window_focus');
    }
    
    /**
     * Gère la perte de focus de la fenêtre
     */
    handleWindowBlur() {
        this.logEvent('window_blur');
    }
    
    /**
     * Gère les changements de visibilité
     */
    handleVisibilityChange() {
        if (document.hidden) {
            this.logEvent('page_hidden');
        } else {
            this.logEvent('page_visible');
        }
    }
    
    /**
     * Gère le redimensionnement de la fenêtre
     */
    handleResize() {
        this.logEvent('window_resize', {
            new_size: `${window.innerWidth}x${window.innerHeight}`,
            screen_size: `${screen.width}x${screen.height}`
        });
    }
    
    /**
     * Gère les touches du clavier
     */
    handleKeyDown(e) {
        // Ignorer les touches de navigation normales
        const ignoredKeys = ['Tab', 'Enter', 'Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
        if (ignoredKeys.includes(e.key)) return;
        
        // Détecter les raccourcis clavier
        const isShortcut = e.ctrlKey || e.metaKey || e.altKey;
        if (isShortcut) {
            this.logEvent('keyboard_shortcut', {
                key: e.key,
                ctrl: e.ctrlKey,
                alt: e.altKey,
                shift: e.shiftKey,
                meta: e.metaKey,
                target: e.target?.tagName || 'unknown'
            });
            
            // Empêcher l'exécution du raccourci
            e.preventDefault();
        }
    }
    
    /**
     * Gère les touches relâchées
     */
    handleKeyUp(e) {
        // Log des touches importantes
        const importantKeys = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'];
        if (importantKeys.includes(e.key)) {
            this.logEvent('keyboard_shortcut', {
                key: e.key,
                target: e.target?.tagName || 'unknown'
            });
        }
    }
    
    /**
     * Gère le clic droit
     */
    handleRightClick(e) {
        this.logEvent('right_click', {
            target: e.target?.tagName || 'unknown',
            x: e.clientX,
            y: e.clientY
        });
        
        // Empêcher le menu contextuel
        e.preventDefault();
    }
    
    /**
     * Gère les tentatives de copie
     */
    handleCopy(e) {
        this.logEvent('copy_attempt', {
            target: e.target?.tagName || 'unknown',
            selection: window.getSelection()?.toString()?.substring(0, 100) || ''
        });
        
        // Empêcher la copie
        e.preventDefault();
    }
    
    /**
     * Gère les tentatives de collage
     */
    handlePaste(e) {
        this.logEvent('paste_attempt', {
            target: e.target?.tagName || 'unknown'
        });
        
        // Empêcher le collage
        e.preventDefault();
    }
    
    /**
     * Gère la perte de connexion
     */
    handleConnectionLost() {
        this.logEvent('connection_lost');
    }
    
    /**
     * Gère la restauration de connexion
     */
    handleConnectionRestored() {
        this.logEvent('connection_restored');
    }
    
    /**
     * Gère les changements de plein écran
     */
    handleFullscreenChange() {
        if (document.fullscreenElement) {
            this.logEvent('fullscreen_enter');
        } else {
            this.logEvent('fullscreen_exit');
        }
    }
    
    /**
     * Gère la soumission de formulaire
     */
    handleFormSubmit(e) {
        this.logEvent('form_submit', {
            form_id: e.target?.id || 'unknown',
            form_action: e.target?.action || 'unknown'
        });
    }
    
    /**
     * Enregistre un événement
     */
    logEvent(eventType, eventData = {}) {
        if (!this.isTracking) return;
        
        const event = {
            event_type: eventType,
            test_id: this.testId,
            question_number: this.currentQuestion,
            event_data: eventData,
            session_id: this.sessionId,
            duration: Date.now() - this.startTime,
            timestamp: new Date().toISOString()
        };
        
        console.log('📝 Événement:', eventType, eventData);
        
        // Ajouter à la queue
        this.eventQueue.push(event);
        
        // Envoyer immédiatement si c'est un événement critique
        const criticalEvents = ['violation_detected', 'copy_attempt', 'paste_attempt', 'right_click', 'keyboard_shortcut', 'dev_tools'];
        if (criticalEvents.includes(eventType)) {
            this.sendEvent(event);
        } else if (this.eventQueue.length >= this.maxQueueSize) {
            this.flushQueue();
        }
    }
    
    /**
     * Envoie un événement au serveur
     */
    async sendEvent(event) {
        try {
            const response = await fetch('/log-test-event/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(event)
            });
            
            if (!response.ok) {
                console.error('❌ Erreur lors de l\'envoi de l\'événement:', response.statusText);
            }
        } catch (error) {
            console.error('❌ Erreur réseau lors de l\'envoi de l\'événement:', error);
        }
    }
    
    /**
     * Vide la queue d'événements
     */
    async flushQueue() {
        if (this.eventQueue.length === 0) return;
        
        const events = [...this.eventQueue];
        this.eventQueue = [];
        
        for (const event of events) {
            await this.sendEvent(event);
        }
    }
    
    /**
     * Démarre l'envoi automatique
     */
    startAutoFlush() {
        if (!this.config.autoFlush) return;
        
        setInterval(() => {
            this.flushQueue();
        }, this.flushInterval);
    }
    
    /**
     * Enregistre une réponse à une question
     */
    logQuestionAnswer(questionNumber, answer, isChange = false) {
        const eventType = isChange ? 'question_change' : 'question_answer';
        this.logEvent(eventType, {
            question_number: questionNumber,
            answer: answer,
            is_change: isChange
        });
    }
    
    /**
     * Enregistre une violation de sécurité
     */
    logSecurityViolation(violationType, details = {}) {
        this.logEvent('violation_detected', {
            violation_type: violationType,
            ...details
        });
    }
    
    /**
     * Termine le tracking
     */
    endTracking() {
        if (!this.isTracking) return;
        
        this.logEvent('test_end', {
            total_duration_ms: Date.now() - this.startTime,
            total_events: this.eventQueue.length
        });
        
        this.flushQueue();
        this.isTracking = false;
        
        console.log('🏁 TestEventTracker arrêté');
    }
    
    /**
     * Génère un ID de session unique
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Récupère le token CSRF
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    /**
     * Met à jour le numéro de question actuel
     */
    setCurrentQuestion(questionNumber) {
        this.currentQuestion = questionNumber;
        this.logEvent('question_view', {
            question_number: questionNumber
        });
    }
}

// Export pour utilisation globale
window.TestEventTracker = TestEventTracker;

// Auto-initialisation si les données sont présentes
document.addEventListener('DOMContentLoaded', function() {
    const testIdElement = document.querySelector('[data-test-id]');
    if (testIdElement) {
        const testId = testIdElement.getAttribute('data-test-id');
        window.testTracker = new TestEventTracker(testId);
        
        // Arrêter le tracking quand l'utilisateur quitte la page
        window.addEventListener('beforeunload', () => {
            if (window.testTracker) {
                window.testTracker.endTracking();
            }
        });
    }
});

console.log('📊 TestEventTracker chargé'); 