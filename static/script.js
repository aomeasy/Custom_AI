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
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show target page
    const targetPage = document.getElementById(pageId + '-page');
    if (targetPage) {
        targetPage.classList.add('active');
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
            <div
