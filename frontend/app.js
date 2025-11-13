/**
 * Polymarket Trading Bot - Enhanced Frontend
 */

// Use Railway production API or localhost for development
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://polymarket-bot-api-production.up.railway.app';

// Global State
let currentUser = null;
let currentUserId = null;
let selectedPosition = null;
let selectedMarket = null;
let selectedMarketData = null; // Store full market data including question
let registrationData = {}; // Stores email/password during registration wizard
let cachedMarkets = []; // Cache markets for trending display
let fullWalletAddress = null; // Store full wallet address for copying
let fullOwnerAddress = null; // Store full owner address for Safe wallets

//==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Polymarket Bot Initialized');
    initializeApp();
});

function initializeApp() {
    // Check if user is logged in
    const storedUser = localStorage.getItem('polybot_user');
    if (storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            currentUserId = currentUser._id || currentUser.id;
            showDashboard();
        } catch (e) {
            console.error('Invalid stored user data');
            localStorage.removeItem('polybot_user');
            showLanding();
        }
    } else {
        showLanding();
    }

    // Event Listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Navigation
    document.getElementById('nav-login')?.addEventListener('click', () => showModal('login-modal'));
    document.getElementById('nav-register')?.addEventListener('click', () => showModal('register-modal'));
    document.getElementById('nav-logout')?.addEventListener('click', handleLogout);
    document.getElementById('hero-get-started')?.addEventListener('click', () => showModal('register-modal'));

    // Brand/logo click - close any open modals
    document.querySelector('.nav-brand')?.addEventListener('click', () => {
        // Close any open modals
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });

        // Scroll to top for clean navigation
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Modal Links
    document.getElementById('show-register')?.addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('login-modal');
        showModal('register-modal');
    });

    document.getElementById('show-login')?.addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('register-modal');
        showModal('login-modal');
    });

    // Auth Forms
    document.getElementById('login-submit')?.addEventListener('click', handleLogin);

    // Registration - Auto create Safe wallet
    document.getElementById('register-next')?.addEventListener('click', handleRegisterNext);

    // Wallet Actions
    document.getElementById('btn-send-funds')?.addEventListener('click', () => {
        document.getElementById('send-funds-section').style.display = 'block';
    });
    document.getElementById('btn-export-key')?.addEventListener('click', exportSafeWalletKeys);
    document.getElementById('copy-address')?.addEventListener('click', copyWalletAddress);
    document.getElementById('copy-owner-address')?.addEventListener('click', copyOwnerAddress);
    document.getElementById('approve-usdc-btn')?.addEventListener('click', handleApproveUSDC);

    // Withdraw Funds Actions
    document.getElementById('confirm-send')?.addEventListener('click', sendFunds);
    document.getElementById('cancel-send')?.addEventListener('click', () => {
        document.getElementById('send-funds-section').style.display = 'none';
        document.getElementById('send-recipient').value = '';
        document.getElementById('send-amount').value = '';
    });

    // Trading
    document.getElementById('position-yes')?.addEventListener('click', () => selectPosition('YES'));
    document.getElementById('position-no')?.addEventListener('click', () => selectPosition('NO'));
    document.getElementById('execute-trade')?.addEventListener('click', executeTrade);
    document.getElementById('load-from-url')?.addEventListener('click', loadMarketFromURL);

    // Advanced Options Toggles
    document.getElementById('enable-stop-loss')?.addEventListener('change', (e) => {
        document.getElementById('stop-loss').disabled = !e.target.checked;
    });
    document.getElementById('enable-take-profit')?.addEventListener('change', (e) => {
        document.getElementById('take-profit').disabled = !e.target.checked;
    });

    // Copy Trading - handle both select and custom input
    document.getElementById('trader-select')?.addEventListener('change', (e) => {
        if (e.target.value) {
            document.getElementById('custom-trader-address').value = '';
        }
    });
    document.getElementById('custom-trader-address')?.addEventListener('input', (e) => {
        if (e.target.value) {
            document.getElementById('trader-select').value = '';
        }
    });
    document.getElementById('start-copy-trading')?.addEventListener('click', startCopyTrading);
    document.getElementById('stop-copy-trading')?.addEventListener('click', stopCopyTrading);

    // Market Search & Filter
    document.getElementById('search-markets-btn')?.addEventListener('click', searchMarkets);
    document.getElementById('market-search')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchMarkets();
    });

    // Bot Trading
    document.getElementById('bot-probability')?.addEventListener('input', (e) => {
        document.getElementById('bot-probability-value').textContent = e.target.value + '%';
    });
    document.getElementById('start-bot')?.addEventListener('click', startBotTrading);
    document.getElementById('stop-bot')?.addEventListener('click', stopBotTrading);
}

//==================== UI FUNCTIONS ====================

function showLanding() {
    document.getElementById('landing').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('nav-login').style.display = 'block';
    document.getElementById('nav-register').style.display = 'block';
    document.getElementById('user-menu').style.display = 'none';
}

function showDashboard() {
    document.getElementById('landing').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('nav-login').style.display = 'none';
    document.getElementById('nav-register').style.display = 'none';
    document.getElementById('user-menu').style.display = 'flex';

    if (currentUser) {
        document.getElementById('user-email').textContent = currentUser.email;
        loadDashboardData();

        // Initialize whale alerts
        if (!whaleInterval) {
            initializeWhaleAlerts();
        }
    }
}

function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
    // Reset registration wizard when opening register modal
    if (modalId === 'register-modal') {
        document.getElementById('register-step-1').style.display = 'block';
        document.getElementById('register-step-2').style.display = 'none';
    }
}

function hideModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification show ${type}`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

//==================== AUTHENTICATION ====================

async function handleRegisterNext() {
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm').value;

    if (!email || !password) {
        showNotification('Please fill in all fields', 'error');
        return;
    }

    if (password !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }

    // Store credentials
    registrationData = { email, password };

    // Show creating wallet step
    document.getElementById('register-step-1').style.display = 'none';
    document.getElementById('register-step-2').style.display = 'block';

    // Automatically create Safe wallet
    await completeRegistration();
}

async function completeRegistration() {
    try {
        showNotification('Creating account with Safe Wallet...', 'info');

        // Register the user with Safe wallet
        const response = await fetch(`${API_URL}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: registrationData.email,
                password: registrationData.password,
                wallet_address: null
            })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            currentUserId = data.user._id || data.user.id;
            localStorage.setItem('polybot_user', JSON.stringify(currentUser));

            hideModal('register-modal');
            showNotification('Account created successfully with Safe Wallet!', 'success');
            showDashboard();
        } else {
            showNotification(data.message || 'Registration failed', 'error');
            // Go back to step 1
            document.getElementById('register-step-2').style.display = 'none';
            document.getElementById('register-step-1').style.display = 'block';
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please try again.', 'error');
        // Go back to step 1
        document.getElementById('register-step-2').style.display = 'none';
        document.getElementById('register-step-1').style.display = 'block';
    }
}

async function handleLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    if (!email || !password) {
        showNotification('Please enter email and password', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            currentUserId = data.user._id || data.user.id;
            localStorage.setItem('polybot_user', JSON.stringify(data.user));

            hideModal('login-modal');
            showNotification('Login successful!', 'success');
            showDashboard();
        } else {
            showNotification(data.message || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please try again.', 'error');
    }
}

function handleLogout() {
    localStorage.removeItem('polybot_user');
    currentUser = null;
    currentUserId = null;
    showLanding();
    showNotification('Logged out successfully', 'success');
}

//==================== DASHBOARD DATA ====================

async function loadDashboardData() {
    await Promise.all([
        loadWalletInfo(),
        loadUserStats(),
        loadMarkets(),
        loadLiveSports(),
        loadTrendingMarkets(),
        loadTopTraders(),
        loadActivity()
    ]);
}

async function loadUserStats() {
    try {
        const response = await fetch(`${API_URL}/users/${currentUserId}/stats`);
        const data = await response.json();

        if (data.success || data.stats) {
            const stats = data.stats || data;

            // Display total volume
            const totalVolume = stats.total_volume || 0;
            document.getElementById('total-volume').textContent = `$${totalVolume.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

            // Display total trades
            const totalTrades = stats.total_trades || 0;
            document.getElementById('total-trades').textContent = totalTrades;

            // Display win rate
            const winRate = stats.win_rate || 0;
            document.getElementById('win-rate').textContent = `${winRate}%`;

            // Display total profit
            const totalProfit = stats.total_profit || 0;
            const profitColor = totalProfit >= 0 ? '#4caf50' : '#f44336';
            const profitElement = document.getElementById('total-profit');
            profitElement.textContent = `$${totalProfit.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            profitElement.style.color = profitColor;
        }
    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

async function loadWalletInfo() {
    try {
        const response = await fetch(`${API_URL}/wallet/${currentUserId}`);
        const data = await response.json();

        if (data.success && data.wallet) {
            const wallet = data.wallet;

            // Store full address for copying
            fullWalletAddress = wallet.wallet_address;

            document.getElementById('wallet-address').textContent =
                wallet.wallet_address ? `${wallet.wallet_address.slice(0, 6)}...${wallet.wallet_address.slice(-4)}` : '-';

            // Display wallet type
            let walletTypeText = '-';
            if (wallet.wallet_type === 'safe') {
                walletTypeText = 'Safe Wallet (Gasless)';

                // Show owner address for Safe wallets
                if (wallet.owner_address) {
                    fullOwnerAddress = wallet.owner_address;
                    document.getElementById('owner-address').textContent =
                        `${wallet.owner_address.slice(0, 6)}...${wallet.owner_address.slice(-4)}`;
                    document.getElementById('owner-address-item').style.display = 'block';
                } else {
                    document.getElementById('owner-address-item').style.display = 'none';
                }
            } else if (wallet.wallet_type === 'imported') {
                walletTypeText = 'Imported Wallet';
                document.getElementById('owner-address-item').style.display = 'none';
            } else if (wallet.wallet_type === 'external') {
                walletTypeText = 'External Wallet';
                document.getElementById('owner-address-item').style.display = 'none';
            } else {
                walletTypeText = wallet.wallet_type || '-';
                document.getElementById('owner-address-item').style.display = 'none';
            }
            document.getElementById('wallet-type').textContent = walletTypeText;

            // Display POL balance
            const polBalance = wallet.pol_balance || wallet.matic_balance || 0;
            document.getElementById('pol-balance').textContent = `${parseFloat(polBalance).toFixed(4)} POL`;

            // Display USDC.e balance
            const usdcBalance = wallet.usdc_balance || 0;
            document.getElementById('usdc-balance').textContent = `${parseFloat(usdcBalance).toFixed(2)} USDC.e`;

            // Display total value
            const totalValue = wallet.total_usd || 0;
            document.getElementById('total-balance').textContent = `$${parseFloat(totalValue).toFixed(2)}`;
        }
    } catch (error) {
        console.error('Error loading wallet:', error);
    }
}

async function loadMarkets() {
    try {
        const response = await fetch(`${API_URL}/markets?limit=50`);
        const data = await response.json();

        if (data.success && data.markets) {
            cachedMarkets = data.markets;
            // Markets are now loaded on click from trending/live sports sections
            // No dropdown needed
        }
    } catch (error) {
        console.error('Error loading markets:', error);
    }
}

async function loadLiveSports() {
    try {
        const response = await fetch(`${API_URL}/markets?limit=100&category=sports&live_only=true`);
        const data = await response.json();

        const sportsDiv = document.getElementById('live-sports');

        if (data.success && data.markets && data.markets.length > 0) {
            sportsDiv.innerHTML = data.markets.map(market => `
                <div class="market-card sport-card" data-market-id="${market.id}" data-market='${JSON.stringify(market)}'>
                    <h4>${market.question}</h4>
                </div>
            `).join('');

            // Add click handlers
            document.querySelectorAll('#live-sports .market-card').forEach(card => {
                card.addEventListener('click', () => {
                    const market = JSON.parse(card.dataset.market);
                    loadMarketIntoTrading(market);
                });
            });
        } else {
            sportsDiv.innerHTML = '<p class="empty-state">No live sports markets available</p>';
        }
    } catch (error) {
        console.error('Error loading live sports:', error);
        document.getElementById('live-sports').innerHTML = '<p class="empty-state">Failed to load sports</p>';
    }
}

async function loadTrendingMarkets() {
    try {
        const response = await fetch(`${API_URL}/markets?limit=12`);
        const data = await response.json();

        const marketsDiv = document.getElementById('trending-markets');

        if (data.success && data.markets && data.markets.length > 0) {
            marketsDiv.innerHTML = data.markets.map(market => `
                <div class="market-card" data-market-id="${market.id}" data-market='${JSON.stringify(market)}'>
                    <h4>${market.question}</h4>
                </div>
            `).join('');

            // Add click handlers
            document.querySelectorAll('.market-card').forEach(card => {
                card.addEventListener('click', () => {
                    const market = JSON.parse(card.dataset.market);
                    loadMarketIntoTrading(market);
                });
            });
        } else {
            marketsDiv.innerHTML = '<p class="empty-state">No markets available</p>';
        }
    } catch (error) {
        console.error('Error loading trending markets:', error);
        document.getElementById('trending-markets').innerHTML = '<p class="empty-state">Failed to load markets</p>';
    }
}

function loadMarketIntoTrading(market) {
    selectedMarket = market.id;
    selectedMarketData = market; // Store full market data

    // Display selected market
    displaySelectedMarket(market);

    // Scroll to trading section smoothly
    const tradingSection = document.querySelector('.trade-form');
    if (tradingSection) {
        tradingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    showNotification(`✅ Market loaded: ${market.question.slice(0, 60)}...`, 'success');
}

function displaySelectedMarket(market) {
    const displayDiv = document.getElementById('selected-market-display');
    const textDiv = document.getElementById('selected-market-text');

    displayDiv.style.display = 'block';
    textDiv.textContent = market.question;
}

async function loadTopTraders() {
    try {
        const response = await fetch(`${API_URL}/traders/top?limit=5`);
        const data = await response.json();

        const tradersDiv = document.getElementById('top-traders');
        const traderSelect = document.getElementById('trader-select');

        if (data.success && data.traders && data.traders.length > 0) {
            tradersDiv.innerHTML = data.traders.map((trader, index) => `
                <div class="trader-item">
                    <strong>#${index + 1} ${trader.address.slice(0, 6)}...${trader.address.slice(-4)}</strong>
                    <span>Win Rate: ${trader.win_rate}% | Trades: ${trader.total_trades}</span>
                </div>
            `).join('');

            traderSelect.innerHTML = '<option value="">Select a trader to copy...</option>';
            data.traders.forEach(trader => {
                const option = document.createElement('option');
                option.value = trader.address;
                option.textContent = `${trader.address.slice(0, 6)}...${trader.address.slice(-4)} (${trader.win_rate}% win rate)`;
                traderSelect.appendChild(option);
            });
        } else {
            tradersDiv.innerHTML = '<p class="empty-state">No traders available</p>';
        }
    } catch (error) {
        console.error('Error loading traders:', error);
        document.getElementById('top-traders').innerHTML = '<p class="empty-state">Failed to load traders</p>';
    }
}

async function loadActivity() {
    try {
        const response = await fetch(`${API_URL}/activity/${currentUserId}?limit=10`);
        const data = await response.json();

        const activityDiv = document.getElementById('activity-feed');

        if (data.success && data.activities && data.activities.length > 0) {
            activityDiv.innerHTML = data.activities.map(activity => `
                <div class="activity-item">
                    <strong>${activity.action}</strong>
                    <small>${new Date(activity.timestamp).toLocaleString()}</small>
                </div>
            `).join('');
        } else {
            activityDiv.innerHTML = '<p class="empty-state">No recent activity</p>';
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

//==================== WALLET FUNCTIONS ====================

async function exportSafeWalletKeys() {
    if (!confirm('⚠️ WARNING: This will export your Safe Wallet owner keys. These keys give full access to your wallet. Never share them with anyone. Continue?')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/wallet/export-key/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: null })
        });

        const data = await response.json();

        if (data.success && data.private_key) {
            // Show Safe wallet details
            let message = `SAFE WALLET KEYS\n\n`;
            message += `Safe Wallet Address: ${data.wallet_address || 'N/A'}\n`;
            message += `Owner Address: ${data.owner_address || 'N/A'}\n\n`;
            message += `Owner Private Key:\n${data.private_key}\n\n`;
            message += `⚠️ KEEP THESE SAFE! Never share with anyone!`;

            // Create a text area to show all info
            const textarea = document.createElement('textarea');
            textarea.value = message;
            textarea.style.position = 'fixed';
            textarea.style.top = '50%';
            textarea.style.left = '50%';
            textarea.style.transform = 'translate(-50%, -50%)';
            textarea.style.width = '500px';
            textarea.style.height = '300px';
            textarea.style.padding = '1rem';
            textarea.style.zIndex = '10000';
            textarea.style.fontFamily = 'monospace';
            textarea.readOnly = true;

            document.body.appendChild(textarea);
            textarea.select();

            // Copy to clipboard
            navigator.clipboard.writeText(message);

            alert('Safe Wallet keys copied to clipboard! Press OK to close.');
            document.body.removeChild(textarea);

            showNotification('Safe Wallet keys exported and copied!', 'success');
        } else {
            showNotification(data.message || data.error || 'Export failed', 'error');
        }
    } catch (error) {
        console.error('Error exporting Safe wallet keys:', error);
        showNotification('Failed to export Safe wallet keys', 'error');
    }
}

async function handleApproveUSDC() {
    if (!currentUserId) {
        showNotification('Please log in first', 'error');
        return;
    }

    const approveBtn = document.getElementById('approve-usdc-btn');
    const originalText = approveBtn.textContent;

    try {
        // Step 1: Check wallet balance first (POL and USDC.e)
        console.log('[APPROVE] Checking wallet balance...');
        approveBtn.disabled = true;
        approveBtn.textContent = 'Checking balance...';

        const walletResponse = await fetch(`${API_URL}/wallet/${currentUserId}`);
        const walletData = await walletResponse.json();

        if (!walletData.success) {
            showNotification('Failed to check wallet balance', 'error');
            approveBtn.disabled = false;
            approveBtn.textContent = originalText;
            return;
        }

        const polBalance = parseFloat(walletData.wallet?.pol_balance || 0);
        const usdcBalance = parseFloat(walletData.wallet?.usdc_balance || 0);
        const walletType = walletData.wallet?.wallet_type || 'unknown';

        console.log('[APPROVE] POL Balance:', polBalance);
        console.log('[APPROVE] USDC.e Balance:', usdcBalance);
        console.log('[APPROVE] Wallet Type:', walletType);

        // Step 2: Check if it's an external wallet
        if (walletType === 'external') {
            approveBtn.disabled = false;
            approveBtn.textContent = originalText;
            showNotification('External wallets approve USDC.e automatically when trading', 'warning');

            alert('External Wallet Detected\n\nFor external wallets (MetaMask, Rabby, etc.), USDC.e approval happens automatically when you make your first trade.\n\nYour wallet will show an approval popup when needed.');
            return;
        }

        // Step 3: Check if user has USDC.e to approve
        if (usdcBalance === 0) {
            approveBtn.disabled = false;
            approveBtn.textContent = originalText;

            const depositMsg = 'You need to deposit USDC.e first!\n\n' +
                               'Current USDC.e Balance: 0.00\n\n' +
                               'Please deposit USDC.e to your wallet address before approving.\n\n' +
                               'Would you like to see how to get USDC.e?';

            if (confirm(depositMsg)) {
                alert('How to Get USDC.e:\n\n' +
                      '1. Bridge USDC from Ethereum to Polygon:\n' +
                      '   https://wallet.polygon.technology/bridge\n\n' +
                      '2. Or buy USDC.e directly on Polygon using:\n' +
                      '   - Uniswap (Polygon)\n' +
                      '   - QuickSwap\n' +
                      '   - Any Polygon DEX\n\n' +
                      '3. Send USDC.e to your wallet address\n\n' +
                      'IMPORTANT: Make sure it\'s USDC.e (bridged USDC), not native USDC!');
            }
            return;
        }

        // Step 4: Check for sufficient gas (POL)
        const MIN_POL_REQUIRED = 0.02;

        if (polBalance < MIN_POL_REQUIRED) {
            approveBtn.disabled = false;
            approveBtn.textContent = originalText;

            const gasMsg = `⛽ Insufficient Gas (POL)\n\n` +
                          `Current POL Balance: ${polBalance.toFixed(4)} POL\n` +
                          `Required: ~${MIN_POL_REQUIRED} POL\n` +
                          `Needed: ${(MIN_POL_REQUIRED - polBalance).toFixed(4)} POL more\n\n` +
                          `USDC.e approval requires ~0.01-0.02 POL for gas fees.\n\n` +
                          `Please deposit POL to your wallet first.\n\n` +
                          `Would you like to see how to get POL?`;

            showNotification(`Insufficient POL for gas. You have ${polBalance.toFixed(4)} POL, need at least ${MIN_POL_REQUIRED} POL`, 'error');

            if (confirm(gasMsg)) {
                const helpMsg = 'How to Get POL (Polygon):\n\n' +
                               '1. Buy POL on exchanges:\n' +
                               '   - Coinbase, Binance, Kraken, etc.\n\n' +
                               '2. Bridge from Ethereum:\n' +
                               '   https://wallet.polygon.technology/bridge\n\n' +
                               '3. Use a faucet (small amounts):\n' +
                               '   https://faucet.polygon.technology\n\n' +
                               `Send POL to your wallet address:\n${walletData.wallet?.wallet_address}\n\n` +
                               'You need ~0.05 POL to be safe for multiple transactions.';

                alert(helpMsg);
            }
            return;
        }

        // Step 5: Check if already approved
        console.log('[APPROVE] Checking current allowance...');
        approveBtn.textContent = 'Checking approval...';

        const allowanceResponse = await fetch(`${API_URL}/wallet/usdc-allowance/${currentUserId}`);
        const allowanceData = await allowanceResponse.json();

        if (allowanceData.success && allowanceData.is_approved) {
            approveBtn.disabled = false;
            approveBtn.textContent = '✓ Already Approved';
            approveBtn.style.background = '#28a745';

            showNotification('USDC.e is already approved! You can trade now.', 'success');
            return;
        }

        // Step 6: Confirm approval
        approveBtn.textContent = originalText;

        const confirmMsg = `Approve USDC.e for trading on Polymarket?\n\n` +
                          `✅ POL Balance: ${polBalance.toFixed(4)} POL (sufficient)\n` +
                          `✅ USDC.e Balance: ${usdcBalance.toFixed(2)} USDC.e\n\n` +
                          `Gas Cost: ~0.01-0.02 POL (~$0.01)\n\n` +
                          `This is a one-time approval. Click OK to proceed.`;

        if (!confirm(confirmMsg)) {
            approveBtn.disabled = false;
            return;
        }

        // Step 7: Execute approval
        console.log('[APPROVE] Executing USDC.e approval...');
        approveBtn.textContent = 'Approving...';

        const response = await fetch(`${API_URL}/wallet/approve-usdc/${currentUserId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        console.log('[APPROVE] Response:', data);

        if (data.success) {
            showNotification('✅ USDC.e approved successfully! You can now trade.', 'success');

            // Show transaction details
            if (data.tx_hash) {
                console.log('[APPROVE] Transaction hash:', data.tx_hash);
                console.log('[APPROVE] Explorer URL:', data.explorer_url);

                const viewTxMsg = `✅ USDC.e Approved Successfully!\n\n` +
                                 `Transaction Hash:\n${data.tx_hash}\n\n` +
                                 `You can now trade on Polymarket!\n\n` +
                                 `View transaction on Polygonscan?`;

                if (confirm(viewTxMsg)) {
                    window.open(data.explorer_url, '_blank');
                }
            }

            // Update button to show approved state
            approveBtn.textContent = '✓ Approved';
            approveBtn.style.background = '#28a745';
            approveBtn.disabled = false;

            // Reload wallet to update balances
            setTimeout(() => {
                loadWallet();
            }, 2000);

        } else {
            // Handle specific error cases
            let errorMsg = 'Approval failed';

            if (data.error) {
                // Check for gas-related errors
                if (data.error.toLowerCase().includes('insufficient') && data.error.toLowerCase().includes('pol')) {
                    errorMsg = `⛽ Insufficient POL for gas fees\n\n${data.error}\n\nPlease deposit more POL to your wallet.`;
                    showNotification(`Insufficient POL: ${data.error}`, 'error');
                } else if (data.error.toLowerCase().includes('gas')) {
                    errorMsg = `⛽ Gas Error\n\n${data.error}`;
                    showNotification(`Gas error: ${data.error}`, 'error');
                } else {
                    errorMsg = data.error;
                    showNotification(data.error, 'error');
                }
            } else {
                errorMsg = data.message || 'Unknown error occurred';
                showNotification(errorMsg, 'error');
            }

            console.error('[APPROVE] Error:', data);
            alert(errorMsg);

            // Re-enable button
            approveBtn.disabled = false;
            approveBtn.textContent = originalText;
        }

    } catch (error) {
        console.error('[APPROVE] Exception:', error);
        showNotification('Network error. Please check your connection and try again.', 'error');

        // Re-enable button
        approveBtn.disabled = false;
        approveBtn.textContent = originalText;
    }
}

function copyWalletAddress() {
    if (!fullWalletAddress) {
        showNotification('No wallet address available', 'error');
        return;
    }

    navigator.clipboard.writeText(fullWalletAddress).then(() => {
        showNotification('Full address copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy address', 'error');
    });
}

function copyOwnerAddress() {
    if (!fullOwnerAddress) {
        showNotification('No owner address available', 'error');
        return;
    }

    navigator.clipboard.writeText(fullOwnerAddress).then(() => {
        showNotification('Owner address copied! Send POL here for gas.', 'success');
    }).catch(() => {
        showNotification('Failed to copy owner address', 'error');
    });
}

async function sendFunds() {
    const tokenType = document.getElementById('send-token-type').value;
    const recipient = document.getElementById('send-recipient').value.trim();
    const amount = parseFloat(document.getElementById('send-amount').value);

    if (!recipient) {
        showNotification('Please enter recipient address', 'error');
        return;
    }

    if (!recipient.startsWith('0x') || recipient.length !== 42) {
        showNotification('Invalid recipient address', 'error');
        return;
    }

    if (!amount || amount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    if (!confirm(`Are you sure you want to send ${amount} ${tokenType.toUpperCase()} to ${recipient}?`)) {
        return;
    }

    try {
        showNotification('Sending funds...', 'info');

        const response = await fetch(`${API_URL}/wallet/send/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                recipient: recipient,
                amount: amount,
                token: tokenType
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Funds sent successfully!', 'success');

            // Show transaction link if available
            if (data.explorer_url) {
                console.log('Transaction:', data.explorer_url);
            }

            document.getElementById('send-funds-section').style.display = 'none';
            document.getElementById('send-recipient').value = '';
            document.getElementById('send-amount').value = '';

            // Reload wallet info
            await loadWalletInfo();
        } else {
            // Show detailed error message
            let errorMsg = data.message || 'Send failed';

            // If it's a gas issue, show the owner address
            if (data.owner_address) {
                errorMsg = data.explanation || errorMsg;
                console.log('Owner address:', data.owner_address);
                console.log('Owner POL balance:', data.owner_pol_balance);
            }

            showNotification(errorMsg, 'error');

            // Show alert with full details if there's an explanation
            if (data.explanation) {
                setTimeout(() => {
                    alert(data.explanation);
                }, 500);
            }
        }
    } catch (error) {
        console.error('Error sending funds:', error);
        showNotification('Failed to send funds', 'error');
    }
}

//==================== TRADING FUNCTIONS ====================

function selectPosition(position) {
    selectedPosition = position;

    // Update UI
    document.querySelectorAll('.btn-position').forEach(btn => {
        btn.classList.remove('active');
    });

    if (position === 'YES') {
        document.getElementById('position-yes').classList.add('active');
    } else {
        document.getElementById('position-no').classList.add('active');
    }
}

async function executeTrade() {
    if (!selectedMarket || !selectedMarketData) {
        showNotification('Please select a market', 'error');
        return;
    }

    if (!selectedPosition) {
        showNotification('Please select YES or NO', 'error');
        return;
    }

    const amount = parseFloat(document.getElementById('trade-amount').value);
    if (!amount || amount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }

    // Get stop loss and take profit if enabled
    const enableStopLoss = document.getElementById('enable-stop-loss').checked;
    const enableTakeProfit = document.getElementById('enable-take-profit').checked;

    const stopLoss = enableStopLoss ? parseFloat(document.getElementById('stop-loss').value) : null;
    const takeProfit = enableTakeProfit ? parseFloat(document.getElementById('take-profit').value) : null;

    try {
        showNotification('Executing trade...', 'info');

        const response = await fetch(`${API_URL}/trades/manual?user_id=${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market_id: selectedMarket,
                market_question: selectedMarketData.question,
                position: selectedPosition,
                amount: amount,
                stop_loss: stopLoss,
                take_profit: takeProfit
            })
        });

        const data = await response.json();

        if (data.success) {
            // Show detailed success message
            let message = '✅ Real trade executed on Polymarket!\n\n';
            if (data.details) {
                message += data.details + '\n';
            }
            if (data.order_id) {
                message += `Order ID: ${data.order_id.substring(0, 8)}...\n`;
            }
            if (data.builder_attributed) {
                message += '🎯 Builder attribution: Active\n';
            }
            message += `\nRemaining balance: $${data.remaining_balance?.toFixed(2) || '0.00'} USDC`;

            showNotification(message, 'success');

            // Reset form
            document.getElementById('trade-amount').value = '';
            document.getElementById('stop-loss').value = '';
            document.getElementById('take-profit').value = '';
            selectedPosition = null;
            selectedMarketData = null;
            document.querySelectorAll('.btn-position').forEach(btn => btn.classList.remove('active'));

            // Reload data
            await loadWalletInfo();
            await loadActivity();
        } else {
            showNotification(data.message || data.error || 'Trade failed', 'error');
        }
    } catch (error) {
        console.error('Error executing trade:', error);
        showNotification('Failed to execute trade', 'error');
    }
}

async function loadMarketFromURL() {
    try {
        const url = document.getElementById('polymarket-url').value.trim();

        if (!url) {
            showNotification('Please paste a Polymarket URL', 'error');
            return;
        }

        // Validate it's a Polymarket URL
        if (!url.includes('polymarket.com')) {
            showNotification('Invalid URL - must be a Polymarket link', 'error');
            return;
        }

        showNotification('Loading market...', 'info');

        // Extract market slug from URL
        // Example URLs:
        // https://polymarket.com/event/will-trump-win-2024
        // https://polymarket.com/event/will-trump-win-2024?tid=123
        // https://polymarket.com/market/will-bitcoin-hit-100k

        let slug = '';
        if (url.includes('/event/')) {
            slug = url.split('/event/')[1].split('?')[0].split('/')[0];
        } else if (url.includes('/market/')) {
            slug = url.split('/market/')[1].split('?')[0].split('/')[0];
        } else {
            showNotification('Could not parse URL - try copying the full market URL', 'error');
            return;
        }

        // Search for the market using the slug
        const response = await fetch(`${API_URL}/markets/search?query=${encodeURIComponent(slug)}&limit=20`);
        const data = await response.json();

        if (!data.success || !data.markets || data.markets.length === 0) {
            showNotification('Market not found - try searching for it in trending markets', 'error');
            return;
        }

        // Find the best match - prefer exact slug match or close match in question
        let market = data.markets[0];

        for (const m of data.markets) {
            if (m.market_slug === slug || m.question.toLowerCase().includes(slug.replace(/-/g, ' '))) {
                market = m;
                break;
            }
        }

        // Load the market into trading
        loadMarketIntoTrading(market);

        showNotification(`Market loaded: ${market.question.substring(0, 50)}...`, 'success');

        // Clear the URL input
        document.getElementById('polymarket-url').value = '';

    } catch (error) {
        console.error('Error loading market from URL:', error);
        showNotification('Failed to load market from URL', 'error');
    }
}

//==================== COPY TRADING FUNCTIONS ====================

async function startCopyTrading() {
    // Get trader address from either select or custom input
    let traderAddress = document.getElementById('trader-select').value;
    const customAddress = document.getElementById('custom-trader-address').value.trim();

    if (customAddress) {
        traderAddress = customAddress;
    }

    const maxAmount = parseFloat(document.getElementById('copy-amount').value);

    if (!traderAddress) {
        showNotification('Please select a trader or enter a wallet address', 'error');
        return;
    }

    if (!maxAmount || maxAmount <= 0) {
        showNotification('Please enter a valid max amount', 'error');
        return;
    }

    try {
        showNotification('Starting copy trading...', 'info');

        const response = await fetch(`${API_URL}/copy-trading/start/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                trader_address: traderAddress,
                max_amount: maxAmount
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Copy trading started!', 'success');
            document.getElementById('copy-status').textContent = `Active (${traderAddress.slice(0, 6)}...${traderAddress.slice(-4)})`;
            document.getElementById('copy-status').style.color = '#28a745';
            document.getElementById('start-copy-trading').style.display = 'none';
            document.getElementById('stop-copy-trading').style.display = 'block';
        } else {
            showNotification(data.error || 'Failed to start copy trading', 'error');
        }
    } catch (error) {
        console.error('Error starting copy trading:', error);
        showNotification('Failed to start copy trading', 'error');
    }
}

async function stopCopyTrading() {
    try {
        showNotification('Stopping copy trading...', 'info');

        const response = await fetch(`${API_URL}/copy-trading/stop/${currentUserId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Copy trading stopped', 'success');
            document.getElementById('copy-status').textContent = 'Inactive';
            document.getElementById('copy-status').style.color = '#666';
            document.getElementById('start-copy-trading').style.display = 'block';
            document.getElementById('stop-copy-trading').style.display = 'none';
        } else {
            showNotification(data.error || 'Failed to stop copy trading', 'error');
        }
    } catch (error) {
        console.error('Error stopping copy trading:', error);
        showNotification('Failed to stop copy trading', 'error');
    }
}

//==================== MARKET SEARCH & FILTER ====================

async function searchMarkets() {
    const searchTerm = document.getElementById('market-search').value.trim();
    const category = document.getElementById('market-category').value;

    try {
        showNotification('Searching all markets...', 'info');

        // Build query parameters - get ALL markets
        let queryParams = '?limit=500';  // Get up to 500 markets (all available)
        if (category) {
            queryParams += `&category=${category}`;
        }

        const response = await fetch(`${API_URL}/markets${queryParams}`);
        const data = await response.json();

        if (data.success && data.markets) {
            let markets = data.markets;

            // Filter by search term if provided
            if (searchTerm) {
                markets = markets.filter(market =>
                    market.question.toLowerCase().includes(searchTerm.toLowerCase())
                );
            }

            displayFilteredMarkets(markets);
            showNotification(`Found ${markets.length} markets`, 'success');
        } else {
            showNotification('Failed to search markets', 'error');
        }
    } catch (error) {
        console.error('Error searching markets:', error);
        showNotification('Search failed', 'error');
    }
}

function displayFilteredMarkets(markets) {
    const marketsDiv = document.getElementById('trending-markets');

    if (markets.length === 0) {
        marketsDiv.innerHTML = '<p class="empty-state">No markets found matching your criteria</p>';
        return;
    }

    marketsDiv.innerHTML = markets.map(market => `
        <div class="market-card" data-market-id="${market.id}" data-market='${JSON.stringify(market)}'>
            <h4>${market.question}</h4>
        </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.market-card').forEach(card => {
        card.addEventListener('click', () => {
            const market = JSON.parse(card.dataset.market);
            loadMarketIntoTrading(market);
        });
    });
}

//==================== BOT TRADING ====================

let botInterval = null;

async function startBotTrading() {
    const category = document.getElementById('bot-category').value;
    const probability = parseInt(document.getElementById('bot-probability').value);
    const amount = parseFloat(document.getElementById('bot-amount').value);
    const stopLoss = parseFloat(document.getElementById('bot-stop-loss').value);
    const takeProfit = parseFloat(document.getElementById('bot-take-profit').value);

    if (!amount || amount <= 0) {
        showNotification('Please enter a valid trade amount', 'error');
        return;
    }

    if (!stopLoss || !takeProfit) {
        showNotification('Please set stop loss and take profit', 'error');
        return;
    }

    try {
        showNotification('Starting bot...', 'info');

        const response = await fetch(`${API_URL}/bot/start/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: category || 'all',
                min_probability: probability,
                amount: amount,
                stop_loss: stopLoss,
                take_profit: takeProfit
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Bot started successfully!', 'success');

            // Update UI
            const botStatus = document.getElementById('bot-status');
            botStatus.textContent = 'Active';
            botStatus.classList.add('active');
            document.getElementById('bot-stats').textContent = `Min: ${probability}% | Amount: $${amount}`;
            document.getElementById('start-bot').style.display = 'none';
            document.getElementById('stop-bot').style.display = 'block';

            // Start monitoring bot
            startBotMonitoring();
        } else {
            showNotification(data.error || 'Failed to start bot', 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('Failed to start bot', 'error');
    }
}

async function stopBotTrading() {
    try {
        showNotification('Stopping bot...', 'info');

        const response = await fetch(`${API_URL}/bot/stop/${currentUserId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Bot stopped', 'success');

            // Update UI
            const botStatus = document.getElementById('bot-status');
            botStatus.textContent = 'Inactive';
            botStatus.classList.remove('active');
            document.getElementById('bot-stats').textContent = '';
            document.getElementById('start-bot').style.display = 'block';
            document.getElementById('stop-bot').style.display = 'none';

            // Stop monitoring
            if (botInterval) {
                clearInterval(botInterval);
                botInterval = null;
            }
        } else {
            showNotification(data.error || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Failed to stop bot', 'error');
    }
}

function startBotMonitoring() {
    // Check bot status every 30 seconds
    botInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/bot/status/${currentUserId}`);
            const data = await response.json();

            if (data.success && data.status) {
                const stats = data.status;
                document.getElementById('bot-stats').textContent =
                    `Trades: ${stats.trades_executed || 0} | Win Rate: ${stats.win_rate || 0}%`;

                // Reload activity to show bot trades
                await loadActivity();
            }
        } catch (error) {
            console.error('Error checking bot status:', error);
        }
    }, 30000); // Check every 30 seconds
}

//==================== WHALE ALERTS ====================

let whaleInterval = null;
let lastWhaleId = null;
let currentWhaleData = null;

function initializeWhaleAlerts() {
    // Set up event listeners for whale alert buttons
    document.getElementById('close-whale-alert')?.addEventListener('click', closeWhaleAlert);
    document.getElementById('whale-trade-btn')?.addEventListener('click', loadWhaleMarket);
    document.getElementById('whale-tweet-btn')?.addEventListener('click', tweetWhaleAlert);

    // Start polling for whale activity
    startWhaleMonitoring();
}

function startWhaleMonitoring() {
    // Poll for whale activity every 15 seconds
    whaleInterval = setInterval(async () => {
        try {
            let queryParams = '';
            if (lastWhaleId) {
                queryParams = `?since=${lastWhaleId}`;
            }

            const response = await fetch(`${API_URL}/whale-activity${queryParams}`);
            const data = await response.json();

            if (data.success && data.whales && data.whales.length > 0) {
                // Filter for buys only and amount > $20,000
                const bigWhales = data.whales.filter(whale =>
                    whale.side === 'BUY' && parseFloat(whale.amount) >= 20000
                );

                if (bigWhales.length > 0) {
                    // Show the first whale alert
                    const whale = bigWhales[0];
                    lastWhaleId = whale.id;
                    showWhaleAlert(whale);
                }
            }
        } catch (error) {
            console.error('Error checking whale activity:', error);
        }
    }, 15000); // Check every 15 seconds
}

function showWhaleAlert(whale) {
    currentWhaleData = whale;

    // Update whale alert content
    document.getElementById('whale-market-title').textContent = whale.market_question || 'Unknown Market';
    document.getElementById('whale-amount').textContent = `$${parseFloat(whale.amount).toLocaleString()}`;
    document.getElementById('whale-position').textContent = whale.position || whale.side;

    // Format time
    const timeAgo = getTimeAgo(whale.timestamp);
    document.getElementById('whale-time').textContent = timeAgo;

    // Show the alert
    const whaleAlert = document.getElementById('whale-alert');
    whaleAlert.style.display = 'block';

    // Auto-hide after 30 seconds
    setTimeout(() => {
        closeWhaleAlert();
    }, 30000);
}

function closeWhaleAlert() {
    document.getElementById('whale-alert').style.display = 'none';
    currentWhaleData = null;
}

function loadWhaleMarket() {
    if (!currentWhaleData) return;

    // Create market object from whale data
    const market = {
        id: currentWhaleData.market_id,
        question: currentWhaleData.market_question,
        probability: currentWhaleData.probability || 0,
        volume: currentWhaleData.volume || 0
    };

    // Load into manual trading
    loadMarketIntoTrading(market);

    // Close whale alert
    closeWhaleAlert();
}

function tweetWhaleAlert() {
    if (!currentWhaleData) return;

    const whale = currentWhaleData;
    const amount = parseFloat(whale.amount).toLocaleString();
    const position = whale.position || whale.side;
    const market = whale.market_question || 'a market';

    // Create tweet text
    const tweetText = `🐋 WHALE ALERT!\n\n$${amount} ${position} on:\n"${market}"\n\nTrade on Polymarket 👇\n#Polymarket #WhaleAlert`;

    // Encode for URL
    const encodedText = encodeURIComponent(tweetText);

    // Open Twitter intent
    window.open(`https://twitter.com/intent/tweet?text=${encodedText}`, '_blank');

    closeWhaleAlert();
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}


