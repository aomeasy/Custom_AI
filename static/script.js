// Application State
let isLoggedIn = false;
let currentUser = '';

// Initialize Application
function initApp() {
    // Check if user is already logged in (you might want to implement proper session management)
    checkLoginStatus();
    
    // Bind event listeners
    bindEventListeners();
    
    // Show appropriate page
    if (!isLoggedIn) {
        showPage('login');
    } else {
        showPage('home');
    }
}

// Event Listeners
function bindEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Chat form
    document.getElementById('chat-form').addEventListener('submit', handleChatMessage);
    
    // Admin helper form
    document.getElementById('admin-form').addEventListener('submit', handleAdminMessage);
    
    // Settings form
    document.getElementById('settings-form').addEventListener('submit', handleSettings);
    
    // Test connection button
    document.getElementById('test-connection').addEventListener('click', testConnection);
    
    // Auto-resize chat input
    const chatInput = document.getElementById('chat-input');
    const adminInput = document.getElementById('admin-input');
    
    [chatInput, adminInput].forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (input === chatInput) {
                    handleChatMessage(e);
                } else {
                    handleAdminMessage(e);
                }
            }
        });
    });
}

// Page Management
function showPage(pageId) {
    console.log('Showing page:', pageId); // เพิ่ม debug log
    
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show target page
    const targetPage = document.getElementById(pageId + '-page');
    if (targetPage) {
        targetPage.classList.add('active');
        console.log('Page found and activated:', pageId); // debug log
    } else {
        console.error('Page not found:', pageId + '-page'); // debug log
    }
    
    // Update navigation
    updateNavigation(pageId);
    
    // Load page-specific data
    if (pageId === 'settings') {
        loadSettings();
    }
}

function updateNavigation(activePageId) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.getElementById('nav-' + activePageId);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Show/hide logout button
    const logoutBtn = document.getElementById('logout-btn');
    const navMenu = document.getElementById('nav-menu');
    
    if (isLoggedIn) {
        logoutBtn.style.display = 'flex';
        navMenu.classList.remove('hidden');
        navMenu.classList.add('flex');
    } else {
        logoutBtn.style.display = 'none';
        navMenu.classList.add('hidden');
        navMenu.classList.remove('flex');
    }
}

// Authentication
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showToast('กรุณากรอกข้อมูลให้ครบถ้วน', 'error');
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            isLoggedIn = true;
            currentUser = username;
            showToast(result.message, 'success');
            showPage('home');
            
            // Clear login form
            document.getElementById('login-form').reset();
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('เกิดข้อผิดพลาดในการเข้าสู่ระบบ', 'error');
    } finally {
        showLoading(false);
    }
}

async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            isLoggedIn = false;
            currentUser = '';
            showToast(result.message, 'success');
            showPage('login');
            
            // Clear chat messages
            clearChatMessages();
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Force logout even if API call fails
        isLoggedIn = false;
        currentUser = '';
        showPage('login');
    }
}

function checkLoginStatus() {
    // This is a simple check - in production you'd validate with the server
    // For now, we'll assume user needs to login each time
    isLoggedIn = false;
}

// Chat Functionality
async function handleChatMessage(e) {
    e.preventDefault();
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator('chat-messages');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            addChatMessage(result.response, 'bot');
        } else {
            addChatMessage(result.error || 'เกิดข้อผิดพลาดในการประมวลผล', 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        addChatMessage('เกิดข้อผิดพลาดในการเชื่อมต่อ โปรดลองใหม่อีกครั้ง', 'bot');
    } finally {
        removeTypingIndicator(typingId);
    }
}

async function handleAdminMessage(e) {
    e.preventDefault();
    
    const input = document.getElementById('admin-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to admin chat
    addAdminMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator('admin-messages');
    
    try {
        const response = await fetch('/api/admin-help', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            addAdminMessage(result.response, 'bot');
        } else {
            addAdminMessage(result.error || 'เกิดข้อผิดพลาดในระบบช่วยเหลือ', 'bot');
        }
    } catch (error) {
        console.error('Admin helper error:', error);
        addAdminMessage('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'bot');
    } finally {
        removeTypingIndicator(typingId);
    }
}

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="flex items-end justify-end space-x-2">
                <div class="message-content">
                    ${escapeHtml(message)}
                </div>
                <div class="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                    <i data-lucide="user" class="w-4 h-4 text-white"></i>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-2">
                <div class="w-8 h-8 bg-gradient-to-r from-amber-400 to-yellow-500 rounded-full flex items-center justify-center">
                    <i data-lucide="bot" class="w-4 h-4 text-white"></i>
                </div>
                <div class="message-content">
                    ${escapeHtml(message).replace(/\n/g, '<br>')}
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Re-initialize icons
    lucide.createIcons();
}

function addAdminMessage(message, sender) {
    const adminMessages = document.getElementById('admin-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender} mb-3`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="flex items-end justify-end space-x-2">
                <div class="bg-blue-500 text-white rounded-lg p-2 text-sm max-w-xs">
                    ${escapeHtml(message)}
                </div>
                <div class="w-6 h-6 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
                    <i data-lucide="user" class="w-3 h-3 text-white"></i>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-2">
                <div class="w-6 h-6 bg-gradient-to-r from-green-400 to-teal-500 rounded-full flex items-center justify-center">
                    <i data-lucide="help-circle" class="w-3 h-3 text-white"></i>
                </div>
                <div class="bg-green-50 rounded-lg p-2 text-sm max-w-xs">
                    ${escapeHtml(message).replace(/\n/g, '<br>')}
                </div>
            </div>
        `;
    }
    
    adminMessages.appendChild(messageDiv);
    adminMessages.scrollTop = adminMessages.scrollHeight;
    
    // Re-initialize icons
    lucide.createIcons();
}

function addTypingIndicator(containerId) {
    const container = document.getElementById(containerId);
    const typingDiv = document.createElement('div');
    const typingId = 'typing-' + Date.now();
    typingDiv.id = typingId;
    typingDiv.className = 'chat-message bot';
    typingDiv.innerHTML = `
        <div class="flex items-start space-x-2">
            <div class="w-8 h-8 bg-gradient-to-r from-gray-400 to-gray-500 rounded-full flex items-center justify-center">
                <i data-lucide="more-horizontal" class="w-4 h-4 text-white"></i>
            </div>
            <div class="bg-gray-100 rounded-lg p-3">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;
    
    lucide.createIcons();
    return typingId;
}

function removeTypingIndicator(typingId) {
    const typingElement = document.getElementById(typingId);
    if (typingElement) {
        typingElement.remove();
    }
}

function clearChatMessages() {
    document.getElementById('chat-messages').innerHTML = `
        <div class="chat-message bot">
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 bg-gradient-to-r from-amber-400 to-yellow-500 rounded-full flex items-center justify-center">
                    <i data-lucide="bot" class="w-4 h-4 text-white"></i>
                </div>
                <div class="message-content">
                    <p>สวัสดีครับ! ฉันพร้อมช่วยคุณค้นหาข้อมูลจาก Google Sheets ได้เลย</p>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('admin-messages').innerHTML = `
        <div class="chat-message bot">
            <div class="flex items-start space-x-2">
                <div class="w-6 h-6 bg-gradient-to-r from-green-400 to-teal-500 rounded-full flex items-center justify-center">
                    <i data-lucide="help-circle" class="w-3 h-3 text-white"></i>
                </div>
                <div class="bg-green-50 rounded-lg p-3 text-sm max-w-xs">
                    <p>สวัสดี! ฉันเป็น Admin Helper พร้อมช่วยเหลือคุณในการใช้งาน พิมพ์ "ช่วย" เพื่อดูคำสั่งที่ใช้ได้</p>
                </div>
            </div>
        </div>
    `;
    
    lucide.createIcons();
}

// Settings Management
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        if (response.ok) {
            document.getElementById('system-prompt').value = settings.system_prompt || '';
            document.getElementById('google-sheet-id').value = settings.google_sheet_id || '';
            document.getElementById('line-token').value = settings.line_token || '';
            document.getElementById('telegram-api').value = settings.telegram_api || '';
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function handleSettings(e) {
    e.preventDefault();
    
    const settings = {
        system_prompt: document.getElementById('system-prompt').value,
        google_sheet_id: document.getElementById('google-sheet-id').value,
        line_token: document.getElementById('line-token').value,
        telegram_api: document.getElementById('telegram-api').value
    };
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(result.message, 'success');
        } else {
            showToast(result.message || 'เกิดข้อผิดพลาดในการบันทึก', 'error');
        }
    } catch (error) {
        console.error('Settings error:', error);
        showToast('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'error');
    } finally {
        showLoading(false);
    }
}

async function testConnection() {
    const connectionStatus = document.getElementById('connection-status');
    const sheetsStatus = document.getElementById('sheets-status');
    const aiStatus = document.getElementById('ai-status');
    
    // Show status panel
    connectionStatus.classList.remove('hidden');
    
    // Reset status
    sheetsStatus.innerHTML = 'Google Sheets: <span class="loading">กำลังทดสอบ...</span>';
    aiStatus.innerHTML = 'AI Model: <span class="loading">กำลังทดสอบ...</span>';
    
    try {
        const response = await fetch('/api/test-connection', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Update status indicators
            sheetsStatus.innerHTML = `Google Sheets: <span class="${result.google_sheets ? 'status-online' : 'status-offline'}">${result.google_sheets ? '✅ เชื่อมต่อสำเร็จ' : '❌ ไม่สามารถเชื่อมต่อได้'}</span>`;
            aiStatus.innerHTML = `AI Model: <span class="${result.ai_model ? 'status-online' : 'status-offline'}">${result.ai_model ? '✅ เชื่อมต่อสำเร็จ' : '❌ ไม่สามารถเชื่อมต่อได้'}</span>`;
            
            showToast(result.message, result.google_sheets && result.ai_model ? 'success' : 'error');
        } else {
            sheetsStatus.innerHTML = 'Google Sheets: <span class="status-offline">❌ ไม่สามารถทดสอบได้</span>';
            aiStatus.innerHTML = 'AI Model: <span class="status-offline">❌ ไม่สามารถทดสอบได้</span>';
            showToast(result.error || 'เกิดข้อผิดพลาดในการทดสอบ', 'error');
        }
    } catch (error) {
        console.error('Connection test error:', error);
        sheetsStatus.innerHTML = 'Google Sheets: <span class="status-offline">❌ เกิดข้อผิดพลาด</span>';
        aiStatus.innerHTML = 'AI Model: <span class="status-offline">❌ เกิดข้อผิดพลาด</span>';
        showToast('เกิดข้อผิดพลาดในการทดสอบการเชื่อมต่อ', 'error');
    }
}

// Utility Functions
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');
    
    // Set message
    toastMessage.textContent = message;
    
    // Set type and icon
    toast.className = `fixed top-20 right-4 glass-card p-4 transform transition-transform z-50 toast-${type}`;
    
    let iconName = 'info';
    switch (type) {
        case 'success':
            iconName = 'check';
            break;
        case 'error':
            iconName = 'x';
            break;
        case 'info':
        default:
            iconName = 'info';
            break;
    }
    
    toastIcon.innerHTML = `<i data-lucide="${iconName}" class="w-4 h-4 text-white"></i>`;
    
    // Show toast
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);
    
    // Hide toast after 3 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full');
    }, 3000);
    
    // Re-initialize icons
    lucide.createIcons();
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Mobile Navigation Toggle (for future mobile menu)
function toggleMobileMenu() {
    const navMenu = document.getElementById('nav-menu');
    navMenu.classList.toggle('hidden');
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + / to focus chat input
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        const chatInput = document.getElementById('chat-input');
        if (chatInput && !chatInput.disabled) {
            chatInput.focus();
        }
    }
    
    // Escape to clear current input
    if (e.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && (activeElement.id === 'chat-input' || activeElement.id === 'admin-input')) {
            activeElement.value = '';
            activeElement.blur();
        }
    }
});

// Auto-save settings on input change (debounced)
let settingsTimeout;
function autoSaveSettings() {
    clearTimeout(settingsTimeout);
    settingsTimeout = setTimeout(() => {
        const settingsForm = document.getElementById('settings-form');
        if (settingsForm && document.getElementById('settings-page').classList.contains('active')) {
            // Only auto-save if we're on the settings page
            handleSettings(new Event('submit'));
        }
    }, 2000);
}

// Bind auto-save to settings inputs
document.addEventListener('DOMContentLoaded', function() {
    const settingsInputs = ['system-prompt', 'google-sheet-id', 'line-token', 'telegram-api'];
    settingsInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', autoSaveSettings);
        }
    });
});

// Handle connection errors gracefully
window.addEventListener('online', function() {
    showToast('เชื่อมต่ออินเทอร์เน็ตแล้ว', 'success');
});

window.addEventListener('offline', function() {
    showToast('ไม่มีการเชื่อมต่ออินเทอร์เน็ต', 'error');
});

// Performance optimization - lazy load chat history
function optimizeChatDisplay() {
    const chatMessages = document.getElementById('chat-messages');
    const messages = chatMessages.querySelectorAll('.chat-message');
    
    // Only show last 50 messages for performance
    if (messages.length > 50) {
        for (let i = 0; i < messages.length - 50; i++) {
            messages[i].style.display = 'none';
        }
    }
}

// Call optimization periodically
setInterval(optimizeChatDisplay, 30000); // Every 30 seconds

// Export functions for global access
window.showPage = showPage;
window.logout = logout;
window.initApp = initApp;

// Webhook Management Functions
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    element.select();
    element.setSelectionRange(0, 99999);
    document.execCommand('copy');
    showToast('คัดลอกแล้ว!', 'success');
}

async function setupLineWebhook() {
    try {
        const webhookUrl = document.getElementById('line-webhook-url').value;
        if (!webhookUrl) {
            showToast('กรุณา Deploy เว็บก่อนเพื่อรับ Webhook URL', 'error');
            return;
        }

        showLoading(true);
        const response = await fetch('/api/setup-line-webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ webhook_url: webhookUrl })
        });

        const result = await response.json();
        
        if (result.success) {
            showToast('กรุณาตั้งค่า URL นี้ใน LINE Developer Console', 'info');
        } else {
            showToast(result.error || 'เกิดข้อผิดพลาด', 'error');
        }
    } catch (error) {
        console.error('LINE webhook setup error:', error);
        showToast('เกิดข้อผิดพลาดในการตั้งค่า LINE Webhook', 'error');
    } finally {
        showLoading(false);
    }
}

async function setupTelegramWebhook() {
    try {
        const webhookUrl = document.getElementById('telegram-webhook-url').value;
        if (!webhookUrl) {
            showToast('กรุณา Deploy เว็บก่อนเพื่อรับ Webhook URL', 'error');
            return;
        }

        showLoading(true);
        const response = await fetch('/api/setup-telegram-webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ webhook_url: webhookUrl })
        });

        const result = await response.json();
        
        if (result.success) {
            showToast(result.message, 'success');
        } else {
            showToast(result.error || 'เกิดข้อผิดพลาด', 'error');
        }
    } catch (error) {
        console.error('Telegram webhook setup error:', error);
        showToast('เกิดข้อผิดพลาดในการตั้งค่า Telegram Webhook', 'error');
    } finally {
        showLoading(false);
    }
}

async function testLineIntegration() {
    try {
        showLoading(true);
        const response = await fetch('/api/test-line', {
            method: 'POST'
        });

        const result = await response.json();
        
        if (result.success) {
            showToast('การเชื่อมต่อ LINE API สำเร็จ!', 'success');
            console.log('LINE Bot Info:', result.bot_info);
        } else {
            showToast(result.error || 'การเชื่อมต่อ LINE ล้มเหลว', 'error');
        }
    } catch (error) {
        console.error('LINE test error:', error);
        showToast('เกิดข้อผิดพลาดในการทดสอบ LINE', 'error');
    } finally {
        showLoading(false);
    }
}

async function testTelegramIntegration() {
    try {
        showLoading(true);
        const response = await fetch('/api/test-telegram', {
            method: 'POST'
        });

        const result = await response.json();
        
        if (result.success) {
            showToast('การเชื่อมต่อ Telegram API สำเร็จ!', 'success');
            console.log('Telegram Bot Info:', result.bot_info);
        } else {
            showToast(result.error || 'การเชื่อมต่อ Telegram ล้มเหลว', 'error');
        }
    } catch (error) {
        console.error('Telegram test error:', error);
        showToast('เกิดข้อผิดพลาดในการทดสอบ Telegram', 'error');
    } finally {
        showLoading(false);
    }
}

// Initialize webhook URLs when page loads
function initializeWebhookUrls() {
    const currentHost = window.location.origin;
    const lineWebhookInput = document.getElementById('line-webhook-url');
    const telegramWebhookInput = document.getElementById('telegram-webhook-url');
    
    if (lineWebhookInput && currentHost !== 'null') {
        lineWebhookInput.value = `${currentHost}/webhook/line`;
    }
    
    if (telegramWebhookInput && currentHost !== 'null') {
        telegramWebhookInput.value = `${currentHost}/webhook/telegram`;
    }
}

// Add webhook URL initialization to the existing initApp function
const originalInitApp = window.initApp;
window.initApp = function() {
    if (originalInitApp) {
        originalInitApp();
    }
    
    // Initialize webhook URLs
    setTimeout(initializeWebhookUrls, 100);
    
    // Add webhook functions to global scope
    window.copyToClipboard = copyToClipboard;
    window.setupLineWebhook = setupLineWebhook;
    window.setupTelegramWebhook = setupTelegramWebhook;
    window.testLineIntegration = testLineIntegration;
    window.testTelegramIntegration = testTelegramIntegration;
};
