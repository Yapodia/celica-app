/**
 * Script de sécurité pour les tests
 * Désactive les fonctions de copier-coller et autres raccourcis clavier
 */

(function() {
    'use strict';

    // Variables globales
    let securityViolations = 0;
    const MAX_VIOLATIONS = 3;
    let isTestActive = true;

    // Fonction pour envoyer une violation de sécurité au serveur
    function logSecurityViolation(violation, violationType) {
        if (!isTestActive) return;

        securityViolations++;
        console.log(`🔒 VIOLATION DÉTECTÉE: ${violation} (${violationType}) - Total: ${securityViolations}/${MAX_VIOLATIONS}`);
        
        // Envoyer la violation au serveur
        fetch('/security-violation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                violation: violation,
                violation_type: violationType,
                url: window.location.href
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('✅ Violation enregistrée:', data);
        })
        .catch(error => {
            console.warn('❌ Erreur lors de l\'enregistrement de la violation:', error);
        });

        // Afficher un avertissement
        showSecurityWarning(violation, securityViolations);

        // Si trop de violations, terminer le test
        if (securityViolations >= MAX_VIOLATIONS) {
            console.log('🚫 MAXIMUM DE VIOLATIONS ATTEINT - TERMINATION DU TEST');
            terminateTestDueToViolations();
        }
    }

    // Fonction pour récupérer le token CSRF
    function getCSRFToken() {
        const token = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return token ? token.value : '';
    }

    // Fonction pour afficher un avertissement de sécurité
    function showSecurityWarning(violation, count) {
        // Supprimer l'ancien avertissement s'il existe
        const existingWarning = document.getElementById('securityWarning');
        if (existingWarning) {
            existingWarning.remove();
        }

        // Créer le nouvel avertissement
        const warning = document.createElement('div');
        warning.id = 'securityWarning';
        warning.className = 'security-warning alert alert-warning alert-dismissible fade show';
        warning.innerHTML = `
            <strong>⚠️ Attention !</strong> 
            <br>Action non autorisée détectée : ${violation}
            <br><small>Violation ${count}/${MAX_VIOLATIONS}</small>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Ajouter au body
        document.body.appendChild(warning);

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (warning.parentNode) {
                warning.remove();
            }
        }, 5000);
    }

    // Fonction pour terminer le test à cause des violations
    function terminateTestDueToViolations() {
        isTestActive = false;
        console.log('🚫 TERMINATION DU TEST - Redirection vers la page de violations');
        
        // Afficher un message d'erreur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger text-center';
        errorDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 10000;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 500px;
        `;
        errorDiv.innerHTML = `
            <h4>🚫 Test interrompu</h4>
            <p>Votre test a été interrompu en raison de violations répétées des règles de sécurité.</p>
            <p><strong>Actions détectées :</strong></p>
            <ul class="text-start">
                <li>Copier-coller</li>
                <li>Raccourcis clavier non autorisés</li>
                <li>Autres actions suspectes</li>
            </ul>
            <p class="mb-0">Redirection automatique dans 3 secondes...</p>
        `;
        
        document.body.appendChild(errorDiv);

        // Rediriger vers la page de violation
        setTimeout(() => {
            window.location.href = '/test/security-violation/';
        }, 3000);
    }

    // Désactiver le copier-coller
    function disableCopyPaste() {
        // Désactiver le copier (Ctrl+C, Cmd+C)
        document.addEventListener('copy', function(e) {
            e.preventDefault();
            logSecurityViolation('Tentative de copie détectée', 'copy_paste');
            return false;
        });

        // Désactiver le coller (Ctrl+V, Cmd+V)
        document.addEventListener('paste', function(e) {
            e.preventDefault();
            logSecurityViolation('Tentative de collage détectée', 'copy_paste');
            return false;
        });

        // Désactiver la coupe (Ctrl+X, Cmd+X)
        document.addEventListener('cut', function(e) {
            e.preventDefault();
            logSecurityViolation('Tentative de coupe détectée', 'copy_paste');
            return false;
        });

        // Désactiver le clic droit
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            logSecurityViolation('Clic droit détecté', 'right_click');
            return false;
        });

        // Désactiver la sélection de texte
        document.addEventListener('selectstart', function(e) {
            // Permettre la sélection dans les champs de saisie
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return true;
            }
            e.preventDefault();
            return false;
        });

        // Désactiver le glisser-déposer
        document.addEventListener('dragstart', function(e) {
            e.preventDefault();
            return false;
        });

        document.addEventListener('drop', function(e) {
            e.preventDefault();
            logSecurityViolation('Glisser-déposer détecté', 'copy_paste');
            return false;
        });
    }

    // Désactiver les raccourcis clavier
    function disableKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Raccourcis à désactiver
            const forbiddenShortcuts = [
                { key: 'c', ctrl: true, description: 'Copier (Ctrl+C)' },
                { key: 'v', ctrl: true, description: 'Coller (Ctrl+V)' },
                { key: 'x', ctrl: true, description: 'Couper (Ctrl+X)' },
                { key: 'a', ctrl: true, description: 'Tout sélectionner (Ctrl+A)' },
                { key: 'z', ctrl: true, description: 'Annuler (Ctrl+Z)' },
                { key: 'y', ctrl: true, description: 'Rétablir (Ctrl+Y)' },
                { key: 'p', ctrl: true, description: 'Imprimer (Ctrl+P)' },
                { key: 's', ctrl: true, description: 'Sauvegarder (Ctrl+S)' },
                { key: 'f', ctrl: true, description: 'Rechercher (Ctrl+F)' },
                { key: 'n', ctrl: true, description: 'Nouveau (Ctrl+N)' },
                { key: 'o', ctrl: true, description: 'Ouvrir (Ctrl+O)' },
                { key: 'w', ctrl: true, description: 'Fermer (Ctrl+W)' },
                { key: 't', ctrl: true, description: 'Nouvel onglet (Ctrl+T)' },
                { key: 'r', ctrl: true, description: 'Actualiser (Ctrl+R)' },
                { key: 'l', ctrl: true, description: 'Barre d\'adresse (Ctrl+L)' },
                { key: 'u', ctrl: true, description: 'Code source (Ctrl+U)' },
                { key: 'i', ctrl: true, description: 'Inspecter (Ctrl+I)' },
                { key: 'j', ctrl: true, description: 'Console (Ctrl+J)' },
                { key: 'k', ctrl: true, description: 'Console (Ctrl+K)' },
                { key: 'm', ctrl: true, description: 'Minimiser (Ctrl+M)' },
                { key: 'Tab', ctrl: true, description: 'Changement d\'onglet (Ctrl+Tab)' },
                { key: 'F1', description: 'Aide (F1)' },
                { key: 'F5', description: 'Actualiser (F5)' },
                { key: 'F11', description: 'Plein écran (F11)' },
                { key: 'F12', description: 'Outils de développement (F12)' },
                { key: 'PrintScreen', description: 'Capture d\'écran (PrintScreen)' },
                { key: 'Insert', description: 'Insérer (Insert)' },
                { key: 'Delete', description: 'Supprimer (Delete)' },
                { key: 'Home', description: 'Début (Home)' },
                { key: 'End', description: 'Fin (End)' },
                { key: 'PageUp', description: 'Page précédente (PageUp)' },
                { key: 'PageDown', description: 'Page suivante (PageDown)' }
            ];

            // Vérifier si le raccourci est interdit
            for (let shortcut of forbiddenShortcuts) {
                if (e.key.toLowerCase() === shortcut.key.toLowerCase() && 
                    (shortcut.ctrl ? (e.ctrlKey || e.metaKey) : !e.ctrlKey && !e.metaKey)) {
                    
                    // Permettre certains raccourcis dans les champs de saisie
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                        const allowedInInputs = ['c', 'v', 'x', 'a', 'z', 'y'];
                        if (allowedInInputs.includes(e.key.toLowerCase())) {
                            continue;
                        }
                    }

                    e.preventDefault();
                    logSecurityViolation(shortcut.description, 'keyboard_shortcut');
                    return false;
                }
            }

            // Désactiver Alt+F4 et autres raccourcis système
            if (e.altKey && e.key === 'F4') {
                e.preventDefault();
                logSecurityViolation('Alt+F4 détecté', 'keyboard_shortcut');
                return false;
            }

            // Désactiver Ctrl+Shift+I (Inspecter)
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'i') {
                e.preventDefault();
                logSecurityViolation('Inspecter (Ctrl+Shift+I) détecté', 'dev_tools');
                return false;
            }

            // Désactiver Ctrl+Shift+C (Inspecter élément)
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'c') {
                e.preventDefault();
                logSecurityViolation('Inspecter élément (Ctrl+Shift+C) détecté', 'dev_tools');
                return false;
            }

            // Désactiver Ctrl+Shift+J (Console)
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'j') {
                e.preventDefault();
                logSecurityViolation('Console (Ctrl+Shift+J) détectée', 'dev_tools');
                return false;
            }
        });
    }

    // Désactiver les outils de développement
    function disableDevTools() {
        // Détecter l'ouverture des outils de développement
        let devtools = {
            open: false,
            orientation: null
        };

        setInterval(() => {
            const threshold = 160;
            const widthThreshold = window.outerWidth - window.innerWidth > threshold;
            const heightThreshold = window.outerHeight - window.innerHeight > threshold;
            
            if (widthThreshold || heightThreshold) {
                if (!devtools.open) {
                    devtools.open = true;
                    logSecurityViolation('Outils de développement détectés', 'dev_tools');
                }
            } else {
                devtools.open = false;
            }
        }, 500);

        // Détecter le changement de focus (sortie de la fenêtre)
        let lastFocusTime = Date.now();
        window.addEventListener('blur', () => {
            lastFocusTime = Date.now();
        });

        window.addEventListener('focus', () => {
            const timeDiff = Date.now() - lastFocusTime;
            if (timeDiff > 1000) { // Plus d'1 seconde
                logSecurityViolation('Changement d\'onglet/fenêtre détecté', 'tab_switch');
            }
        });
    }

    // Désactiver la sortie du plein écran
    function disableFullscreenExit() {
        document.addEventListener('fullscreenchange', function() {
            if (!document.fullscreenElement) {
                logSecurityViolation('Sortie du mode plein écran détectée', 'fullscreen_exit');
            }
        });
    }

    // Désactiver les captures d'écran
    function disableScreenshots() {
        // Détecter les tentatives de capture d'écran via les raccourcis
        document.addEventListener('keydown', function(e) {
            if (e.key === 'PrintScreen' || 
                (e.ctrlKey && e.shiftKey && e.key === '3') || // Mac
                (e.ctrlKey && e.shiftKey && e.key === '4')) { // Mac
                e.preventDefault();
                logSecurityViolation('Tentative de capture d\'écran détectée', 'screenshot');
                return false;
            }
        });
    }

    // Masquer le texte sélectionné
    function hideSelectedText() {
        document.addEventListener('selectionchange', function() {
            const selection = window.getSelection();
            if (selection.toString().length > 0) {
                // Masquer temporairement la sélection
                const range = selection.getRangeAt(0);
                const span = document.createElement('span');
                span.style.cssText = 'background: transparent !important; color: transparent !important;';
                range.surroundContents(span);
                
                // Restaurer après un court délai
                setTimeout(() => {
                    if (span.parentNode) {
                        span.parentNode.replaceChild(document.createTextNode(span.textContent), span);
                    }
                }, 100);
            }
        });
    }

    // Initialisation
    function initSecurity() {
        console.log('🔒 Initialisation de la sécurité du test...');
        
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setupSecurity();
            });
        } else {
            setupSecurity();
        }
    }

    function setupSecurity() {
        // Vérifier si nous sommes sur une page de test
        if (!window.location.href.includes('/test/passer/')) {
            return;
        }

        // Activer toutes les protections
        disableCopyPaste();
        disableKeyboardShortcuts();
        disableDevTools();
        disableFullscreenExit();
        disableScreenshots();
        hideSelectedText();

        // Afficher un message de sécurité
        showSecurityNotice();

        console.log('✅ Sécurité du test activée');
    }

    // Afficher un avis de sécurité
    function showSecurityNotice() {
        const notice = document.createElement('div');
        notice.className = 'security-notice';
        notice.innerHTML = `
            <div class="container">
                <i class="fas fa-shield-alt me-2"></i>
                Mode sécurisé activé - Copier-coller et raccourcis clavier désactivés
                <span class="badge bg-warning ms-2">Sécurité</span>
            </div>
        `;
        document.body.insertBefore(notice, document.body.firstChild);
    }

    // Désactiver la sécurité (pour les instructeurs)
    function disableSecurity() {
        isTestActive = false;
        console.log('🔓 Sécurité du test désactivée');
    }

    // Exposer les fonctions publiques
    window.TestSecurity = {
        init: initSecurity,
        disable: disableSecurity,
        logViolation: logSecurityViolation,
        // Fonction de test pour simuler des violations (à supprimer en production)
        testViolation: function() {
            console.log('🧪 TEST: Simulation d\'une violation de sécurité');
            logSecurityViolation('Test de violation simulée', 'test');
        }
    };

    // Initialiser automatiquement
    initSecurity();
    
    // Ajouter une touche de test (Ctrl+Shift+T) pour simuler des violations
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            console.log('🧪 Touche de test activée');
            window.TestSecurity.testViolation();
        }
    });

})(); 