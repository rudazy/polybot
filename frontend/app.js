/**
 * Polymarket Trading Bot - Frontend JavaScript - FIXED VERSION
 */

// API Base URL
const API_URL = 'http://localhost:8000';

// Global state
let currentUser = null;
let currentUserId = null;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Polymarket Bot Dashboard Initialized');
    
    // Check if user is logged in
    const savedUser = localStorage.getItem('polybot_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        currentUserId = currentUser.id;
        showDashboard();
    } else {
        showAuthModal();
    }
    
    // Initialize event listeners AFTER DOM is loaded
    setTimeout(initEventListeners, 100);
});

// ==================== EVENT LISTENERS ====================

function initEventListeners() {
    console.log('Initializing event listeners...');
    
    // Auth tabs - FIXED
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginTab) {
        loginTab.addEventListener('click', function() {
            console.log('Login tab clicked');
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.style.display = 'flex';
            registerForm.style.display = 'none';
        });
    }
    
    if (registerTab) {
        registerTab.addEventListener('click', function() {
            console.log('Register tab clicked');
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.style.display = 'flex';
            loginForm.style.display = 'none';
        });
    }
    
    // Auth actions
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const disconnectBtn = document.getElementById('disconnect-btn');
    
    if (loginBtn) loginBtn.addEventListener('click', handleLogin);
    if (registerBtn) registerBtn.addEventListener('click', handleRegister);
    if (disconnectBtn) disconnectBtn.addEventListener('click', handleDisconnect);
    
    // Bot controls
    const startBtn = document.getElementById('start-bot-btn');
    const stopBtn = document.getElementById('stop-bot-btn');
    if (startBtn) startBtn.addEventListener('click', startBot);
    if (stopBtn) stopBtn.addEventListener('click', stopBot);
    
    // Manual trading
    const executeBtn = document.getElementById('execute-trade-btn');
    if (executeBtn) executeBtn.addEventListener('click', executeManualTrade);
    
    // Markets
    const refreshBtn = document.getElementById('refresh-markets-btn');
    const searchInput = document.getElementById('market-search');
    if (refreshBtn) refreshBtn.addEventListener('click', loadMarkets);
    if (searchInput) searchInput.addEventListener('input', handleMarketSearch);
    
    // Probability slider
    const probSlider = document.getElementById('probability-slider');
    if (probSlider) {
        probSlider.addEventListener('input', (e) => {
            document.getElementById('prob-value').textContent = e.target.value + '%';
        });
    }
    
    // Points redemption
    document.querySelectorAll('.btn-redeem').forEach(btn => {
        btn.addEventListener('click', () => {
            const points = parseInt(btn.dataset.points);
            const reward = btn.dataset.reward;
            redeemPoints(points, reward);
        });
    });
    
    console.log('✅ Event listeners initialized');
}

// ==================== AUTHENTICATION ====================

async function handleLogin() {
    const email = document.getElementById('login-email').value.trim();
    
    if (!email) {
        alert('Please enter your email');
        return;
    }
    
    console.log('Attempting login for:', email);
    
    try {
        const response = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        console.log('Login response:', data);
        
        if (data.success) {
            currentUser = data.user;
            currentUserId = data.user.id;
            localStorage.setItem('polybot_user', JSON.stringify(data.user));
            showDashboard();
            showNotification('✅ Login successful!', 'success');
        } else {
            showNotification('❌ Login failed. User not found.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('❌ Login failed. Please check API server.', 'error');
    }
}

async function handleRegister() {
    const email = document.getElementById('register-email').value.trim();
    const wallet = document.getElementById('register-wallet').value.trim();
    
    if (!email) {
        alert('Please enter your email');
        return;
    }
    
    console.log('Attempting registration for:', email);
    
    try {
        const response = await fetch(`${API_URL}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email, 
                wallet_address: wallet || null 
            })
        });
        
        const data = await response.json();
        console.log('Register response:', data);
        
        if (data.success) {
            currentUser = data.user;
            currentUserId = data.user.id;
            localStorage.setItem('polybot_user', JSON.stringify(data.user));
            showDashboard();
            showNotification('🎉 Account created! 7-day trial started!', 'success');
        } else {
            showNotification('❌ Registration failed. Email may already exist.', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('❌ Registration failed. Please check API server.', 'error');
    }
}

function handleDisconnect() {
    localStorage.removeItem('polybot_user');
    currentUser = null;
    currentUserId = null;
    location.reload();
}

// ==================== UI DISPLAY ====================

function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    
    updateUserInterface();
    loadStats();
    loadMarkets();
    loadActivity();
    loadSettings();
    loadPoints();
    checkBotStatus();
    
    // Auto-refresh every 10 seconds
    setInterval(() => {
        loadStats();
        loadActivity();
        loadPoints();
    }, 10000);
}

function updateUserInterface() {
    if (currentUser.wallet_address) {
        const shortAddress = currentUser.wallet_address.slice(0, 6) + '...' + currentUser.wallet_address.slice(-4);
        document.getElementById('wallet-address').textContent = shortAddress;
    } else {
        document.getElementById('wallet-address').textContent = currentUser.email.split('@')[0];
    }
    
    document.getElementById('disconnect-btn').style.display = 'block';
}

// ==================== LOAD DATA ====================

async function loadStats() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/users/${currentUserId}/stats`);
        const stats = await response.json();
        
        document.getElementById('total-profit').textContent = `$${stats.total_profit.toFixed(2)}`;
        document.getElementById('win-rate').textContent = `${stats.win_rate.toFixed(1)}%`;
        document.getElementById('total-trades').textContent = stats.total_trades;
        document.getElementById('active-positions').textContent = stats.active_positions;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadMarkets() {
    const container = document.getElementById('markets-container');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading markets...</div>';
    
    try {
        const response = await fetch(`${API_URL}/markets?limit=10`);
        const data = await response.json();
        
        if (data.success && data.markets.length > 0) {
            container.innerHTML = '';
            data.markets.forEach(market => {
                const marketCard = createMarketCard(market);
                container.appendChild(marketCard);
            });
        } else {
            container.innerHTML = '<p class="no-data">No markets available</p>';
        }
    } catch (error) {
        console.error('Error loading markets:', error);
        container.innerHTML = '<p class="no-data">Failed to load markets</p>';
    }
}

function createMarketCard(market) {
    const div = document.createElement('div');
    div.className = 'market-card';
    
    const probability = Math.max(market.yes_price || 0.5, market.no_price || 0.5) * 100;
    const probClass = probability >= 75 ? 'high' : 'medium';
    
    div.innerHTML = `
        <div class="market-question">${market.question || 'Unknown Market'}</div>
        <div class="market-info">
            <span>Vol: $${((market.volume || 0) / 1000).toFixed(1)}K</span>
            <span class="market-probability ${probClass}">${probability.toFixed(0)}%</span>
        </div>
    `;
    
    return div;
}

async function loadActivity() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/activity/${currentUserId}?limit=5`);
        const data = await response.json();
        
        const container = document.getElementById('activity-feed');
        if (!container) return;
        
        if (data.success && data.activity.length > 0) {
            container.innerHTML = '';
            data.activity.forEach(item => {
                const activityItem = createActivityItem(item);
                container.appendChild(activityItem);
            });
        } else {
            container.innerHTML = '<p class="no-data">No recent activity</p>';
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

function createActivityItem(item) {
    const div = document.createElement('div');
    div.className = 'activity-item';
    
    const icon = item.action.includes('Bought') ? '📈' : '📉';
    const profitClass = item.profit >= 0 ? 'positive' : 'negative';
    const profitSign = item.profit >= 0 ? '+' : '';
    
    div.innerHTML = `
        <div class="activity-icon">${icon}</div>
        <div class="activity-content">
            <strong>${item.market}</strong>
            <small>${item.action} · ${item.status}</small>
        </div>
        <div class="activity-profit ${profitClass}">
            ${profitSign}$${item.profit.toFixed(2)}
        </div>
    `;
    
    return div;
}

async function loadSettings() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/settings/${currentUserId}`);
        const settings = await response.json();
        
        document.getElementById('category-filter').value = settings.category_filter;
        document.getElementById('probability-slider').value = settings.min_probability * 100;
        document.getElementById('prob-value').textContent = (settings.min_probability * 100) + '%';
        document.getElementById('position-size').value = settings.position_size;
        document.getElementById('max-trades').value = settings.max_daily_trades;
        document.getElementById('min-liquidity').value = settings.min_liquidity;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function loadPoints() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/points/${currentUserId}`);
        const data = await response.json();
        
        document.getElementById('user-points').textContent = data.points_balance.toLocaleString();
        document.getElementById('points-balance').textContent = data.points_balance.toLocaleString();
        
        updateRedeemButtons(data.points_balance);
    } catch (error) {
        console.error('Error loading points:', error);
    }
}

function updateRedeemButtons(points) {
    document.querySelectorAll('.btn-redeem').forEach(btn => {
        const required = parseInt(btn.dataset.points);
        if (points >= required) {
            btn.disabled = false;
            btn.textContent = 'Redeem';
        } else {
            btn.disabled = true;
            btn.textContent = `Need ${(required - points).toLocaleString()}`;
        }
    });
}

// ==================== BOT CONTROLS ====================

async function startBot() {
    await saveSettings();
    
    try {
        const response = await fetch(`${API_URL}/bot/start/${currentUserId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('bot-status').innerHTML = `
                <span class="status-dot online"></span>
                <span>Online</span>
            `;
            document.getElementById('start-bot-btn').style.display = 'none';
            document.getElementById('stop-bot-btn').style.display = 'block';
            showNotification('✅ Bot started successfully!', 'success');
        } else {
            showNotification('❌ ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('❌ Failed to start bot', 'error');
    }
}

async function stopBot() {
    try {
        const response = await fetch(`${API_URL}/bot/stop/${currentUserId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('bot-status').innerHTML = `
                <span class="status-dot offline"></span>
                <span>Offline</span>
            `;
            document.getElementById('start-bot-btn').style.display = 'block';
            document.getElementById('stop-bot-btn').style.display = 'none';
            showNotification('⏸ Bot stopped', 'info');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
    }
}

async function checkBotStatus() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/bot/status/${currentUserId}`);
        const data = await response.json();
        
        if (data.is_running) {
            document.getElementById('bot-status').innerHTML = `
                <span class="status-dot online"></span>
                <span>Online</span>
            `;
            document.getElementById('start-bot-btn').style.display = 'none';
            document.getElementById('stop-bot-btn').style.display = 'block';
        }
    } catch (error) {
        console.error('Error checking bot status:', error);
    }
}

async function saveSettings() {
    const settings = {
        min_probability: parseFloat(document.getElementById('probability-slider').value) / 100,
        category_filter: document.getElementById('category-filter').value,
        position_size: parseFloat(document.getElementById('position-size').value),
        max_daily_trades: parseInt(document.getElementById('max-trades').value),
        min_liquidity: parseFloat(document.getElementById('min-liquidity').value)
    };
    
    try {
        await fetch(`${API_URL}/settings/${currentUserId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
    } catch (error) {
        console.error('Error saving settings:', error);
    }
}

// ==================== MANUAL TRADING ====================

async function executeManualTrade() {
    const market = document.getElementById('manual-market').value;
    const amount = parseFloat(document.getElementById('manual-amount').value);
    const position = document.getElementById('manual-position').value;
    
    if (!market || !amount) {
        showNotification('❌ Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/trades/manual?user_id=${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market_question: market,
                amount: amount,
                position: position
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`✅ Trade executed! +${data.points_earned} points`, 'success');
            document.getElementById('manual-market').value = '';
            document.getElementById('manual-amount').value = '';
            loadStats();
            loadActivity();
            loadPoints();
        } else {
            showNotification('❌ Trade failed', 'error');
        }
    } catch (error) {
        console.error('Error executing trade:', error);
        showNotification('❌ Trade failed', 'error');
    }
}

// ==================== POINTS REDEMPTION ====================

async function redeemPoints(points, reward) {
    if (!confirm(`Redeem ${points.toLocaleString()} points for ${reward}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/points/redeem?user_id=${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: points, reward: reward })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`🎉 Successfully redeemed ${reward}!`, 'success');
            loadPoints();
        } else {
            showNotification('❌ Insufficient points', 'error');
        }
    } catch (error) {
        console.error('Error redeeming points:', error);
        showNotification('❌ Redemption failed', 'error');
    }
}

// ==================== SEARCH ====================

function handleMarketSearch(e) {
    const query = e.target.value.toLowerCase();
    const marketCards = document.querySelectorAll('.market-card');
    
    marketCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? 'block' : 'none';
    });
}

// ==================== NOTIFICATIONS ====================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        z-index: 3000;
        font-weight: 600;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

console.log('✅ App.js loaded successfully');