/**
 * Polymarket Trading Bot - Frontend JavaScript with Wallet Integration & Private Key Export
 */

// API Base URL - Auto-detect environment
const API_URL = 'https://polymarket-bot-api-production.up.railway.app';

// Global state
let currentUser = null;
let currentUserId = null;
let hasWallet = false;
let currentNetwork = 'testnet'; // Default to testnet for safety
let copyTradingActive = false;

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Polymarket Bot Dashboard Initialized');

    // Check if user is logged in
    const savedUser = localStorage.getItem('polybot_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        currentUserId = currentUser.id;
        checkWalletAndProceed();
    } else {
        // Show dashboard in demo mode without login
        showDashboardDemo();
    }

    // Initialize event listeners
    setTimeout(initEventListeners, 100);
});

// ==================== EVENT LISTENERS ====================

function initEventListeners() {
    console.log('Initializing event listeners...');
    
    // Auth tabs
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginTab) {
        loginTab.addEventListener('click', function() {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.style.display = 'flex';
            registerForm.style.display = 'none';
        });
    }
    
    if (registerTab) {
        registerTab.addEventListener('click', function() {
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
    const loginRegisterBtn = document.getElementById('login-register-btn');
    const closeAuthModal = document.getElementById('close-auth-modal');
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    const resetPasswordBtn = document.getElementById('reset-password-btn');
    const cancelResetBtn = document.getElementById('cancel-reset-btn');

    if (loginBtn) loginBtn.addEventListener('click', handleLogin);
    if (registerBtn) registerBtn.addEventListener('click', handleRegister);
    if (disconnectBtn) disconnectBtn.addEventListener('click', handleDisconnect);
    if (loginRegisterBtn) loginRegisterBtn.addEventListener('click', showAuthModal);
    if (closeAuthModal) closeAuthModal.addEventListener('click', hideAuthModal);
    if (forgotPasswordLink) forgotPasswordLink.addEventListener('click', showForgotPasswordModal);
    if (resetPasswordBtn) resetPasswordBtn.addEventListener('click', handlePasswordReset);
    if (cancelResetBtn) cancelResetBtn.addEventListener('click', hideForgotPasswordModal);

    // Close modal when clicking outside
    const authModal = document.getElementById('auth-modal');
    if (authModal) {
        authModal.addEventListener('click', (e) => {
            if (e.target === authModal) {
                hideAuthModal();
            }
        });
    }
    
    // Wallet actions
    const createWalletBtn = document.getElementById('create-wallet-btn');
    const connectMetaMaskBtn = document.getElementById('connect-metamask-btn');
    const refreshBalanceBtn = document.getElementById('refresh-balance-btn');
    const exportKeyBtn = document.getElementById('export-key-btn');
    
    if (createWalletBtn) createWalletBtn.addEventListener('click', handleCreateInAppWallet);
    if (connectMetaMaskBtn) connectMetaMaskBtn.addEventListener('click', handleConnectMetaMask);
    if (refreshBalanceBtn) refreshBalanceBtn.addEventListener('click', loadWalletBalance);
    if (exportKeyBtn) exportKeyBtn.addEventListener('click', handleExportPrivateKey);
    
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

    // Network switcher
    const networkToggleBtn = document.getElementById('network-toggle-btn');
    if (networkToggleBtn) networkToggleBtn.addEventListener('click', handleNetworkSwitch);

    // Top traders
    const refreshTradersBtn = document.getElementById('refresh-traders-btn');
    if (refreshTradersBtn) refreshTradersBtn.addEventListener('click', loadTopTraders);

    // Copy trading
    const startCopyBtn = document.getElementById('start-copy-btn');
    const stopCopyBtn = document.getElementById('stop-copy-btn');
    if (startCopyBtn) startCopyBtn.addEventListener('click', startCopyTrading);
    if (stopCopyBtn) stopCopyBtn.addEventListener('click', stopCopyTrading);
    
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
    const password = document.getElementById('login-password').value;

    if (!email) {
        alert('Please enter your email');
        return;
    }

    if (!password) {
        alert('Please enter your password');
        return;
    }

    console.log('Attempting login for:', email);

    try {
        const response = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        console.log('Login response:', data);

        if (data.success) {
            currentUser = data.user;
            currentUserId = data.user.id;
            localStorage.setItem('polybot_user', JSON.stringify(data.user));
            showNotification('✅ Login successful!', 'success');
            checkWalletAndProceed();
        } else {
            showNotification('❌ Login failed. ' + (data.message || 'Invalid credentials.'), 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('❌ Login failed. Please check API server.', 'error');
    }
}

async function handleRegister() {
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const passwordConfirm = document.getElementById('register-password-confirm').value;

    if (!email) {
        alert('Please enter your email');
        return;
    }

    if (!password) {
        alert('Please enter a password');
        return;
    }

    if (password.length < 6) {
        alert('Password must be at least 6 characters');
        return;
    }

    if (password !== passwordConfirm) {
        alert('Passwords do not match');
        return;
    }

    console.log('Attempting registration for:', email);

    try {
        const response = await fetch(`${API_URL}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, wallet_address: null })
        });

        const data = await response.json();
        console.log('Register response:', data);

        if (data.success) {
            currentUser = data.user;
            currentUserId = data.user.id;
            localStorage.setItem('polybot_user', JSON.stringify(data.user));
            showNotification('🎉 Account created! Completely FREE forever!', 'success');
            checkWalletAndProceed();
        } else {
            showNotification('❌ Registration failed. ' + (data.message || 'Email may already exist.'), 'error');
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
    hasWallet = false;
    location.reload();
}

function showForgotPasswordModal(e) {
    e.preventDefault();
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('forgot-password-modal').style.display = 'flex';
}

function hideForgotPasswordModal() {
    document.getElementById('forgot-password-modal').style.display = 'none';
    document.getElementById('auth-modal').style.display = 'flex';
}

async function handlePasswordReset() {
    const email = document.getElementById('reset-email').value.trim();
    const newPassword = document.getElementById('reset-new-password').value;
    const confirmPassword = document.getElementById('reset-confirm-password').value;

    if (!email) {
        alert('Please enter your email');
        return;
    }

    if (!newPassword) {
        alert('Please enter a new password');
        return;
    }

    if (newPassword.length < 6) {
        alert('Password must be at least 6 characters');
        return;
    }

    if (newPassword !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }

    try {
        showNotification('Resetting password...', 'info');

        const response = await fetch(`${API_URL}/users/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, new_password: newPassword })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Password reset successful! Please login.', 'success');
            // Clear the form
            document.getElementById('reset-email').value = '';
            document.getElementById('reset-new-password').value = '';
            document.getElementById('reset-confirm-password').value = '';
            // Go back to login
            hideForgotPasswordModal();
        } else {
            showNotification('❌ ' + (data.message || 'Password reset failed'), 'error');
        }
    } catch (error) {
        console.error('Password reset error:', error);
        showNotification('❌ Password reset failed. Please check API server.', 'error');
    }
}

// ==================== WALLET FLOW ====================

async function checkWalletAndProceed() {
    try {
        const response = await fetch(`${API_URL}/wallet/${currentUserId}`);
        const data = await response.json();
        
        if (data.success && data.wallet) {
            hasWallet = true;
            showDashboard();
            updateWalletDisplay(data.wallet);
        } else {
            showWalletModal();
        }
    } catch (error) {
        console.error('Error checking wallet:', error);
        showWalletModal();
    }
}

async function handleCreateInAppWallet() {
    try {
        // If no user is logged in, create a guest account first
        if (!currentUserId) {
            showNotification('🔐 Creating guest account...', 'info');
            const guestEmail = `guest_${Date.now()}@polybot.finance`;
            const guestPassword = `guest_${Math.random().toString(36).slice(2)}`;

            const registerResponse = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: guestEmail,
                    password: guestPassword
                })
            });

            const registerData = await registerResponse.json();

            if (registerData.success) {
                currentUserId = registerData.user_id;
                currentUser = { id: currentUserId, email: guestEmail };
                localStorage.setItem('polybot_user', JSON.stringify(currentUser));
            } else {
                showNotification('❌ Failed to create guest account', 'error');
                return;
            }
        }

        showNotification('🔐 Creating your wallet...', 'info');

        const response = await fetch(`${API_URL}/wallet/create-inapp/${currentUserId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ Wallet created successfully!', 'success');
            hasWallet = true;
            showDashboard();
            loadWalletBalance();
        } else {
            showNotification('❌ Failed to create wallet', 'error');
        }
    } catch (error) {
        console.error('Error creating wallet:', error);
        showNotification('❌ Failed to create wallet: ' + error.message, 'error');
    }
}

async function handleConnectMetaMask() {
    if (typeof window.ethereum === 'undefined') {
        showNotification('❌ MetaMask is not installed. Please install it first.', 'error');
        window.open('https://metamask.io/download/', '_blank');
        return;
    }

    try {
        showNotification('🦊 Connecting to MetaMask...', 'info');

        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const walletAddress = accounts[0];

        // If no user is logged in, create a guest account first
        if (!currentUserId) {
            showNotification('🔐 Creating guest account...', 'info');
            const guestEmail = `guest_${Date.now()}@polybot.finance`;
            const guestPassword = `guest_${Math.random().toString(36).slice(2)}`;

            const registerResponse = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: guestEmail,
                    password: guestPassword
                })
            });

            const registerData = await registerResponse.json();

            if (registerData.success) {
                currentUserId = registerData.user_id;
                currentUser = { id: currentUserId, email: guestEmail };
                localStorage.setItem('polybot_user', JSON.stringify(currentUser));
            } else {
                showNotification('❌ Failed to create guest account', 'error');
                return;
            }
        }

        const response = await fetch(`${API_URL}/wallet/connect-external/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: walletAddress })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('✅ MetaMask connected successfully!', 'success');
            hasWallet = true;
            showDashboard();
            loadWalletBalance();
        } else {
            showNotification('❌ Failed to connect wallet', 'error');
        }
    } catch (error) {
        console.error('Error connecting MetaMask:', error);
        showNotification('❌ Failed to connect MetaMask: ' + error.message, 'error');
    }
}

async function loadWalletBalance() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`${API_URL}/wallet/${currentUserId}`);
        const data = await response.json();
        
        if (data.success && data.wallet) {
            updateWalletDisplay(data.wallet);
        }
    } catch (error) {
        console.error('Error loading wallet balance:', error);
    }
}

function updateWalletDisplay(wallet) {
    const shortAddress = wallet.wallet_address.slice(0, 6) + '...' + wallet.wallet_address.slice(-4);
    document.getElementById('wallet-address').textContent = shortAddress;
    
    const walletTypeBadge = document.getElementById('wallet-type-badge');
    if (walletTypeBadge) {
        walletTypeBadge.textContent = wallet.wallet_type === 'in-app' ? '🚀 In-App Wallet' : '🦊 MetaMask';
    }
    
    const walletAddressDisplay = document.getElementById('wallet-address-display');
    if (walletAddressDisplay) {
        walletAddressDisplay.textContent = wallet.wallet_address;
    }
    
    const usdcBalance = document.getElementById('usdc-balance');
    if (usdcBalance) {
        usdcBalance.textContent = `$${wallet.usdc_balance.toFixed(2)}`;
    }
    
    const maticBalance = document.getElementById('matic-balance');
    if (maticBalance) {
        maticBalance.textContent = wallet.matic_balance.toFixed(4);
    }
    
    const exportKeyBtn = document.getElementById('export-key-btn');
    if (exportKeyBtn) {
        if (wallet.wallet_type === 'in-app') {
            exportKeyBtn.style.display = 'block';
        } else {
            exportKeyBtn.style.display = 'none';
        }
    }
}

// ==================== PRIVATE KEY EXPORT ====================

async function handleExportPrivateKey() {
    const confirm1 = confirm(
        "⚠️ WARNING: You are about to export your private key!\n\n" +
        "This is EXTREMELY DANGEROUS if not handled properly.\n\n" +
        "Are you sure you want to continue?"
    );

    if (!confirm1) return;

    const confirm2 = confirm(
        "⚠️ FINAL WARNING:\n\n" +
        "• NEVER share your private key with ANYONE\n" +
        "• Anyone with your private key can steal ALL your funds\n" +
        "• Make sure you're in a private location\n" +
        "• Save it in a secure password manager\n\n" +
        "Do you understand the risks?"
    );

    if (!confirm2) return;

    // Prompt for password verification
    const password = prompt("Enter your password to verify:");

    if (!password) {
        showNotification('❌ Password required to export private key', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/wallet/export-key/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        const data = await response.json();

        if (data.success) {
            showPrivateKeyModal(data.private_key);
        } else {
            showNotification('❌ ' + (data.message || 'Cannot export private key'), 'error');
        }
    } catch (error) {
        console.error('Error exporting private key:', error);
        showNotification('❌ Failed to export private key', 'error');
    }
}

function showPrivateKeyModal(privateKey) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <h2 style="color: #ef4444;">🔑 Your Private Key</h2>
            <p style="color: #f59e0b; margin: 1rem 0;">
                ⚠️ KEEP THIS EXTREMELY SAFE! Never share it with anyone!
            </p>
            
            <div style="background: #0f0f23; padding: 1rem; border-radius: 10px; margin: 1.5rem 0; border: 1px solid #ef4444;">
                <code id="private-key-display" style="
                    word-break: break-all;
                    color: #10b981;
                    font-size: 0.9rem;
                    display: block;
                    font-family: 'Courier New', monospace;
                ">${privateKey}</code>
            </div>
            
            <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
                <button class="btn-primary" id="copy-key-btn" style="flex: 1;">
                    📋 Copy to Clipboard
                </button>
                <button class="btn-danger" id="close-key-modal" style="flex: 1;">
                    Close
                </button>
            </div>
            
            <p style="color: #a0a0c0; font-size: 0.85rem; margin-top: 1rem; text-align: center;">
                💡 Import this key into MetaMask or any Web3 wallet to access your funds
            </p>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('copy-key-btn').addEventListener('click', () => {
        navigator.clipboard.writeText(privateKey);
        showNotification('✅ Private key copied to clipboard!', 'success');
    });
    
    document.getElementById('close-key-modal').addEventListener('click', () => {
        modal.remove();
    });
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// ==================== UI DISPLAY ====================

function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('wallet-modal').style.display = 'none';
}

function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

function showWalletModal() {
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('wallet-modal').style.display = 'flex';
}

function showDashboardDemo() {
    // Show dashboard without login
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('wallet-modal').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';

    // Load public data
    loadMarkets();
    loadTopTraders();

    // Start whale activity notifications
    startWhaleActivityPolling();

    // Show login/register button
    document.getElementById('login-register-btn').style.display = 'block';
}

function showDashboard() {
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('wallet-modal').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';

    updateUserInterface();
    loadStats();
    loadMarkets();
    loadActivity();
    loadSettings();
    loadPoints();
    loadWalletBalance();
    checkBotStatus();
    loadTopTraders();
    loadNetworkStatus();

    setInterval(() => {
        loadStats();
        loadActivity();
        loadPoints();
        loadWalletBalance();
    }, 10000);

    // Start whale activity notifications
    startWhaleActivityPolling();
}

function updateUserInterface() {
    // Show user elements
    document.getElementById('login-register-btn').style.display = 'none';
    document.getElementById('points-display').style.display = 'flex';
    document.getElementById('wallet-badge').style.display = 'flex';
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

        // Load stop loss and take profit
        if (settings.stop_loss !== undefined) {
            document.getElementById('stop-loss').value = settings.stop_loss;
        }
        if (settings.take_profit !== undefined) {
            document.getElementById('take-profit').value = settings.take_profit;
        }
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
        min_liquidity: parseFloat(document.getElementById('min-liquidity').value),
        stop_loss: parseFloat(document.getElementById('stop-loss').value),
        take_profit: parseFloat(document.getElementById('take-profit').value)
    };

    try {
        await fetch(`${API_URL}/settings/${currentUserId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        showNotification('✅ Settings saved with stop loss and take profit', 'success');
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

// ==================== NETWORK SWITCHING ====================

async function loadNetworkStatus() {
    try {
        const response = await fetch(`${API_URL}/network/status/${currentUserId}`);
        const data = await response.json();

        if (data.success) {
            currentNetwork = data.network;
            updateNetworkDisplay(data.network);
        }
    } catch (error) {
        console.error('Error loading network status:', error);
        // Default to testnet if error
        updateNetworkDisplay('testnet');
    }
}

async function handleNetworkSwitch() {
    const newNetwork = currentNetwork === 'testnet' ? 'mainnet' : 'testnet';

    const confirmSwitch = confirm(
        newNetwork === 'mainnet'
            ? '⚠️ WARNING: You are about to switch to MAINNET.\n\nThis will use REAL money and REAL funds.\n\nMake sure you have:\n✓ Tested everything on testnet\n✓ Sufficient MATIC for gas fees\n✓ Real USDC for trading\n\nContinue to mainnet?'
            : '🧪 Switching to TESTNET (Safe Mode)\n\nYou will use test tokens only.\nPerfect for testing strategies!\n\nContinue?'
    );

    if (!confirmSwitch) return;

    try {
        showNotification(`Switching to ${newNetwork}...`, 'info');

        const response = await fetch(`${API_URL}/network/switch/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ network: newNetwork })
        });

        const data = await response.json();

        if (data.success) {
            currentNetwork = newNetwork;
            updateNetworkDisplay(newNetwork);
            showNotification(`✅ Switched to ${newNetwork === 'mainnet' ? 'MAINNET' : 'TESTNET'}!`, 'success');
            loadWalletBalance(); // Refresh balances for new network
        } else {
            showNotification('❌ Failed to switch network', 'error');
        }
    } catch (error) {
        console.error('Error switching network:', error);
        showNotification('❌ Failed to switch network', 'error');
    }
}

function updateNetworkDisplay(network) {
    const networkStatus = document.getElementById('network-status');
    if (networkStatus) {
        if (network === 'mainnet') {
            networkStatus.innerHTML = '🟢 Mainnet';
            networkStatus.style.color = '#10b981';
        } else {
            networkStatus.innerHTML = '🧪 Testnet';
            networkStatus.style.color = '#f59e0b';
        }
    }
}

// ==================== TOP TRADERS ====================

async function loadTopTraders() {
    const container = document.getElementById('top-traders-list');
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading top traders...</div>';

    try {
        const response = await fetch(`${API_URL}/traders/top?limit=5`);
        const data = await response.json();

        if (data.success && data.traders.length > 0) {
            container.innerHTML = '';

            // Update copy trader dropdown
            const copySelect = document.getElementById('copy-trader-select');
            if (copySelect) {
                copySelect.innerHTML = '<option value="">Choose a trader...</option>';
                data.traders.forEach(trader => {
                    const option = document.createElement('option');
                    option.value = trader.wallet_address;
                    option.textContent = `${trader.wallet_address.slice(0, 8)}... - ${trader.win_rate.toFixed(1)}% WR`;
                    copySelect.appendChild(option);
                });
            }

            data.traders.forEach((trader, index) => {
                const traderCard = createTraderCard(trader, index + 1);
                container.appendChild(traderCard);
            });
        } else {
            container.innerHTML = '<p class="no-data">No traders found yet</p>';
        }
    } catch (error) {
        console.error('Error loading top traders:', error);
        container.innerHTML = '<p class="no-data">Failed to load traders</p>';
    }
}

function createTraderCard(trader, rank) {
    const div = document.createElement('div');
    div.className = 'trader-card';

    const rankEmoji = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `#${rank}`;
    const shortAddress = trader.wallet_address.slice(0, 6) + '...' + trader.wallet_address.slice(-4);

    div.innerHTML = `
        <div class="trader-rank">${rankEmoji}</div>
        <div class="trader-info">
            <div class="trader-address">${shortAddress}</div>
            <div class="trader-stats">
                <span class="win-rate ${trader.win_rate >= 70 ? 'high' : 'medium'}">
                    ${trader.win_rate.toFixed(1)}% WR
                </span>
                <span class="trades-count">${trader.total_trades} trades</span>
            </div>
            <div class="trader-profit ${trader.total_profit >= 0 ? 'positive' : 'negative'}">
                ${trader.total_profit >= 0 ? '+' : ''}$${trader.total_profit.toFixed(2)}
            </div>
        </div>
        <button class="btn-copy-small" data-address="${trader.wallet_address}">
            Copy
        </button>
    `;

    // Add click handler for copy button
    const copyBtn = div.querySelector('.btn-copy-small');
    copyBtn.addEventListener('click', () => {
        document.getElementById('copy-trader-select').value = trader.wallet_address;
        showNotification(`Selected trader ${shortAddress}`, 'success');
    });

    return div;
}

// ==================== COPY TRADING ====================

async function startCopyTrading() {
    const manualWallet = document.getElementById('copy-wallet-input').value.trim();
    const selectedTrader = document.getElementById('copy-trader-select').value;
    const copyAmount = parseFloat(document.getElementById('copy-amount').value);
    const maxTrades = parseInt(document.getElementById('max-copy-trades').value);

    // Determine which wallet to use
    let targetWallet = '';

    if (manualWallet) {
        // Validate wallet address format
        if (!manualWallet.startsWith('0x') || manualWallet.length !== 42) {
            showNotification('❌ Invalid wallet address format. Must be 42 characters starting with 0x', 'error');
            return;
        }
        targetWallet = manualWallet;
    } else if (selectedTrader) {
        targetWallet = selectedTrader;
    } else {
        showNotification('❌ Please enter a wallet address or select a trader to copy', 'error');
        return;
    }

    if (!copyAmount || copyAmount <= 0) {
        showNotification('❌ Please enter a valid copy amount', 'error');
        return;
    }

    try {
        showNotification('Starting copy trading...', 'info');

        const response = await fetch(`${API_URL}/copy-trading/start/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                target_wallet: targetWallet,
                copy_amount: copyAmount,
                max_trades_per_day: maxTrades
            })
        });

        const data = await response.json();

        if (data.success) {
            copyTradingActive = true;
            document.getElementById('copy-trade-status').style.display = 'flex';
            document.getElementById('copy-trade-status').innerHTML = `
                <span class="status-dot online"></span>
                <span>Copying: ${targetWallet.slice(0, 8)}...</span>
            `;
            document.getElementById('start-copy-btn').style.display = 'none';
            document.getElementById('stop-copy-btn').style.display = 'block';
            showNotification('✅ Copy trading started!', 'success');
        } else {
            showNotification('❌ ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error starting copy trading:', error);
        showNotification('❌ Failed to start copy trading', 'error');
    }
}

async function stopCopyTrading() {
    try {
        const response = await fetch(`${API_URL}/copy-trading/stop/${currentUserId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            copyTradingActive = false;
            document.getElementById('copy-trade-status').style.display = 'none';
            document.getElementById('start-copy-btn').style.display = 'block';
            document.getElementById('stop-copy-btn').style.display = 'none';
            showNotification('⏸ Copy trading stopped', 'info');
        }
    } catch (error) {
        console.error('Error stopping copy trading:', error);
        showNotification('❌ Failed to stop copy trading', 'error');
    }
}

// ==================== WHALE NOTIFICATIONS ====================

let whaleNotificationQueue = [];
let lastWhaleId = 0;

function showWhaleNotification(whaleData) {
    const container = document.getElementById('whale-notifications');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = 'whale-notification';
    notification.dataset.whaleId = whaleData.id;

    const shortWallet = whaleData.wallet.slice(0, 6) + '...' + whaleData.wallet.slice(-4);
    const positionClass = whaleData.position.toLowerCase();

    notification.innerHTML = `
        <div class="whale-header">
            <div class="whale-icon">🐋</div>
            <div class="whale-badge">Whale Alert</div>
            <button class="whale-close">×</button>
        </div>
        <div class="whale-content">
            <div class="whale-wallet">${shortWallet}</div>
            <div class="whale-action">
                just bought <span class="whale-position ${positionClass}">${whaleData.position}</span> with
                <span class="whale-amount">$${whaleData.amount.toLocaleString()}</span>
            </div>
            <div class="whale-market">${whaleData.market}</div>
            <div class="whale-actions">
                <button class="whale-btn whale-trade-btn" data-whale='${JSON.stringify(whaleData)}'>
                    📈 Trade Now
                </button>
                <button class="whale-btn whale-share-btn" data-whale='${JSON.stringify(whaleData)}'>
                    🐦 Share on X
                </button>
            </div>
        </div>
    `;

    // Add close handler
    const closeBtn = notification.querySelector('.whale-close');
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dismissWhaleNotification(notification);
    });

    // Add trade handler
    const tradeBtn = notification.querySelector('.whale-trade-btn');
    tradeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const whale = JSON.parse(e.target.dataset.whale);
        handleWhaleTradeClick(whale);
    });

    // Add share handler
    const shareBtn = notification.querySelector('.whale-share-btn');
    shareBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const whale = JSON.parse(e.target.dataset.whale);
        handleWhaleShareClick(whale);
    });

    // Auto-dismiss after 15 seconds (increased from 10 to give time to interact)
    setTimeout(() => {
        dismissWhaleNotification(notification);
    }, 15000);

    container.appendChild(notification);

    // Limit to 3 notifications max
    const notifications = container.querySelectorAll('.whale-notification');
    if (notifications.length > 3) {
        dismissWhaleNotification(notifications[0]);
    }
}

function handleWhaleTradeClick(whaleData) {
    // Show trade modal with pre-filled data
    showNotification(`🐋 Opening trade for: ${whaleData.market}`, 'info');

    // Scroll to manual trading section
    const manualTradeCard = document.querySelector('.manual-trade-card');
    if (manualTradeCard) {
        manualTradeCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Pre-fill the position and amount
        setTimeout(() => {
            const positionSelect = document.getElementById('trade-position');
            const amountInput = document.getElementById('trade-amount');

            if (positionSelect) {
                positionSelect.value = whaleData.position;
            }

            if (amountInput) {
                // Suggest a smaller amount than the whale (e.g., 10% of whale amount)
                const suggestedAmount = Math.round(whaleData.amount * 0.1);
                amountInput.value = suggestedAmount;
            }

            // Highlight the section
            manualTradeCard.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.5)';
            setTimeout(() => {
                manualTradeCard.style.boxShadow = '';
            }, 2000);
        }, 500);
    }
}

function handleWhaleShareClick(whaleData) {
    // Create X (Twitter) share URL
    const websiteUrl = 'https://polybot.finance';
    const tweetText = `🐋 Whale Alert! A whale just bought ${whaleData.position} with $${whaleData.amount.toLocaleString()} on: ${whaleData.market}\n\nFollow the smart money and trade now at ${websiteUrl}`;

    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;

    // Open in new window
    window.open(twitterUrl, '_blank', 'width=550,height=420');

    showNotification('🐦 Opening X (Twitter) to share...', 'success');
}

function dismissWhaleNotification(notification) {
    if (!notification || notification.classList.contains('dismissing')) return;

    notification.classList.add('dismissing');
    setTimeout(() => {
        notification.remove();
    }, 500);
}

async function loadWhaleActivity() {
    try {
        const response = await fetch(`${API_URL}/whale-activity?since=${lastWhaleId}`);
        const data = await response.json();

        if (data.success && data.whales.length > 0) {
            data.whales.forEach(whale => {
                showWhaleNotification(whale);
                if (whale.id > lastWhaleId) {
                    lastWhaleId = whale.id;
                }
            });
        }
    } catch (error) {
        console.error('Error loading whale activity:', error);
    }
}

function startWhaleActivityPolling() {
    // Load immediately
    loadWhaleActivity();

    // Poll every 15 seconds
    setInterval(loadWhaleActivity, 15000);
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

console.log('✅ App.js with wallet integration and private key export loaded successfully');