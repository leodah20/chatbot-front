/**
 * Sistema de Toasts Flutuantes
 * Cria notificações temporárias que desaparecem automaticamente
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Cria o container de toasts se não existir
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    /**
     * Exibe um toast
     * @param {string} message - Mensagem a ser exibida
     * @param {string} type - Tipo do toast: 'success', 'error', 'info', 'warning'
     * @param {number} duration - Duração em milissegundos (padrão: 5000)
     */
    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        
        // Ícone baseado no tipo
        const icon = this.getIcon(type);
        
        // Botão de fechar
        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '×';
        closeBtn.setAttribute('aria-label', 'Fechar');
        closeBtn.onclick = () => this.remove(toast);
        
        // Conteúdo do toast
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span class="toast-message">${message}</span>
            </div>
        `;
        
        toast.appendChild(closeBtn);
        this.container.appendChild(toast);
        
        // Anima entrada
        requestAnimationFrame(() => {
            toast.classList.add('toast-show');
        });
        
        // Remove automaticamente após a duração
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toast);
            }, duration);
        }
        
        return toast;
    }

    /**
     * Remove um toast com animação
     */
    remove(toast) {
        if (!toast || !toast.parentNode) return;
        
        toast.classList.remove('toast-show');
        toast.classList.add('toast-hide');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300); // Tempo da animação de saída
    }

    /**
     * Retorna o ícone SVG baseado no tipo
     */
    getIcon(type) {
        const icons = {
            success: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16.6667 5L7.50004 14.1667L3.33337 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            error: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            info: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 13.3333V10M10 6.66667H10.0083M18.3333 10C18.3333 14.6024 14.6024 18.3333 10 18.3333C5.39763 18.3333 1.66667 14.6024 1.66667 10C1.66667 5.39763 5.39763 1.66667 10 1.66667C14.6024 1.66667 18.3333 5.39763 18.3333 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
            warning: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 6.66667V10M10 13.3333H10.0083M18.3333 10C18.3333 14.6024 14.6024 18.3333 10 18.3333C5.39763 18.3333 1.66667 14.6024 1.66667 10C1.66667 5.39763 5.39763 1.66667 10 1.66667C14.6024 1.66667 18.3333 5.39763 18.3333 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        };
        return icons[type] || icons.info;
    }

    /**
     * Limpa todos os toasts
     */
    clear() {
        const toasts = this.container.querySelectorAll('.toast');
        toasts.forEach(toast => this.remove(toast));
    }
}

// Inicializa o gerenciador de toasts
const toastManager = new ToastManager();

// Controle global de mensagens já processadas (evita duplicatas)
const processedMessages = new Set();
const processedElements = new WeakSet();

/**
 * Função global para exibir toasts (compatibilidade com Flask flash messages)
 * Verifica duplicatas antes de exibir
 */
function showToast(message, type = 'info', duration = 5000) {
    // Cria uma chave única para a mensagem (tipo + texto normalizado)
    const messageKey = `${type}:${message.trim().toLowerCase()}`;
    
    // Verifica se já foi exibida recentemente (últimos 2 segundos)
    if (processedMessages.has(messageKey)) {
        return null; // Já foi exibida, não mostra novamente
    }
    
    // Marca como processada
    processedMessages.add(messageKey);
    
    // Remove a chave após 3 segundos para permitir a mesma mensagem em momentos diferentes
    setTimeout(() => {
        processedMessages.delete(messageKey);
    }, 3000);
    
    return toastManager.show(message, type, duration);
}

/**
 * Função auxiliar para detectar tipo de mensagem
 */
function detectMessageType(element) {
    const classList = Array.from(element.classList);
    const text = element.textContent.toLowerCase();
    const computedStyle = window.getComputedStyle(element);
    const bgColor = computedStyle.backgroundColor;
    
    // Detecta por classe
    if (classList.some(c => c.includes('error') || c.includes('red'))) {
        return 'error';
    }
    if (classList.some(c => c.includes('success') || c.includes('green'))) {
        return 'success';
    }
    if (classList.some(c => c.includes('warning') || c.includes('yellow'))) {
        return 'warning';
    }
    if (classList.some(c => c.includes('info') || c.includes('blue'))) {
        return 'info';
    }
    
    // Detecta por texto (mensagens comuns)
    if (text.includes('erro') || text.includes('negado') || text.includes('inválid') || 
        text.includes('falhou') || text.includes('não encontrado')) {
        return 'error';
    }
    if (text.includes('sucesso') || text.includes('cadastrado') || text.includes('atualizado') || 
        text.includes('criado') || text.includes('bem-vindo')) {
        return 'success';
    }
    if (text.includes('aviso') || text.includes('atenção') || text.includes('cuidado')) {
        return 'warning';
    }
    
    return 'info';
}

// Processa mensagens flash imediatamente quando possível (para redirecionamentos)
(function processEarlyMessages() {
    let attempts = 0;
    const maxAttempts = 15;
    
    const checkAndProcess = function() {
        try {
            if (!document.body) {
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkAndProcess, 30);
                }
                return;
            }
            
            const containers = document.querySelectorAll('.flash-messages');
            containers.forEach(container => {
                const messages = container.querySelectorAll('.flash-message-item, div, p, span');
                messages.forEach(msg => {
                    // Verifica se o elemento já foi processado
                    if (processedElements.has(msg) || msg.hasAttribute('data-toast-processed')) {
                        return;
                    }
                    
                    const message = msg.textContent.trim();
                    if (message && message.length > 3) {
                        const type = detectMessageType(msg);
                        const toast = showToast(message, type, type === 'error' ? 6000 : 5000);
                        
                        // Se o toast foi criado (não era duplicata), marca o elemento
                        if (toast) {
                            processedElements.add(msg);
                            msg.setAttribute('data-toast-processed', 'true');
                            msg.style.display = 'none';
                        }
                    }
                });
            });
        } catch (e) {
            // Ignora erros
        }
    };
    
    // Inicia verificação imediatamente
    checkAndProcess();
    setTimeout(checkAndProcess, 50);
    setTimeout(checkAndProcess, 150);
})();

/**
 * Processa mensagens flash do Flask automaticamente
 */
function processFlashMessages() {
    // Procura por mensagens flash em elementos com classes específicas
    const selectors = [
        '.flash-message-item',
        '.message-box',
        '.alert',
        '[role="alert"]',
        '.flash-messages div',
        '.messages-area div',
        'div[class*="message"]',
        'div[class*="alert"]'
    ];
    
    selectors.forEach(selector => {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Verifica se já foi processado
                if (processedElements.has(element) || element.hasAttribute('data-toast-processed')) {
                    return;
                }
                
                const message = element.textContent.trim();
                if (!message || message.length < 3) return;
                
                // Ignora elementos que são containers
                if (element.children.length > 2 && message.length < 50) return;
                
                const type = detectMessageType(element);
                const duration = type === 'error' ? 6000 : 5000;
                
                // Exibe o toast (função já verifica duplicatas)
                const toast = showToast(message, type, duration);
                
                // Se o toast foi criado, marca o elemento como processado
                if (toast) {
                    processedElements.add(element);
                    element.setAttribute('data-toast-processed', 'true');
                    element.style.display = 'none';
                    
                    if (element.parentElement && element.parentElement.classList.contains('flash-messages')) {
                        element.parentElement.style.display = 'none';
                    }
                    if (element.parentElement && element.parentElement.classList.contains('messages-area')) {
                        element.parentElement.style.display = 'none';
                    }
                }
            });
        } catch (e) {
            console.warn('Erro ao processar mensagens flash:', e);
        }
    });
    
    // Processa containers de mensagens flash
    const flashContainers = document.querySelectorAll('.flash-messages, .messages-area');
    flashContainers.forEach(container => {
        if (container.style.display === 'none') return;
        
        const messages = container.querySelectorAll('div, p, span');
        let hasMessages = false;
        
        messages.forEach(msg => {
            // Verifica se já foi processado
            if (processedElements.has(msg) || msg.hasAttribute('data-toast-processed')) {
                return;
            }
            
            const message = msg.textContent.trim();
            if (message && message.length > 3) {
                const type = detectMessageType(msg);
                const toast = showToast(message, type, type === 'error' ? 6000 : 5000);
                
                if (toast) {
                    processedElements.add(msg);
                    msg.setAttribute('data-toast-processed', 'true');
                    hasMessages = true;
                }
            }
        });
        
        // Oculta o container se processou mensagens
        if (hasMessages) {
            setTimeout(() => {
                container.style.display = 'none';
            }, 300);
        }
    });
}

// Processa mensagens quando o DOM estiver pronto (apenas uma vez)
let hasProcessedOnReady = false;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (!hasProcessedOnReady) {
            hasProcessedOnReady = true;
            // Processa imediatamente quando o DOM estiver pronto
            processFlashMessages();
        }
    });
} else {
    // DOM já está carregado, processa imediatamente (apenas uma vez)
    if (!hasProcessedOnReady) {
        hasProcessedOnReady = true;
        processFlashMessages();
    }
}

// Processa também após a página estar completamente carregada (backup, se necessário)
window.addEventListener('load', function() {
    // Já foi processado antes? Não processa novamente
    if (!hasProcessedOnReady) {
        setTimeout(processFlashMessages, 50);
    }
});
