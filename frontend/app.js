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

// ==================== THEME MANAGEMENT ====================

function initTheme() {
    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('polybot_theme') || 'light';
    setTheme(savedTheme);

    // Add theme toggle event listener
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('polybot_theme', theme);

    // Update icon
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Polymarket Bot Dashboard Initialized');

    // Initialize theme
    initTheme();

    // Check if user is logged in
    const savedUser = localStorage.getItem('polybot_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        currentUserId = currentUser.id;
        // Hide landing page, show dashboard
        document.getElementById('landing-page').style.display = 'none';
        document.querySelector('.container').style.display = 'block';
        checkWalletAndProceed();
    } else {
        // Show landing page (not logged in)
        showLandingPage();
    }

    // Initialize event listeners
    setTimeout(initEventListeners, 100);

    // Test that global functions are accessible
    setTimeout(() => {
        console.log('[TEST] window.handleRegister exists:', typeof window.handleRegister);
        console.log('[TEST] window.handleLogin exists:', typeof window.handleLogin);

        // Make test function available in console
        window.testRegisterButton = function() {
            console.log('[TEST] Testing register button click...');
            showAuthModal();
            switchTab('register');
            setTimeout(() => {
                const btn = document.getElementById('register-btn');
                console.log('[TEST] Button found:', btn);
                console.log('[TEST] Button onclick:', btn ? btn.onclick : 'N/A');
                console.log('[TEST] Simulating click event...');
                btn.click();
                console.log('[TEST] After click simulation');
            }, 200);
        };

        window.testRegisterDirect = function() {
            console.log('[TEST] Calling handleRegister directly...');
            window.handleRegister();
        };

        console.log('[TEST] Run testRegisterButton() or testRegisterDirect() in console to test');
    }, 500);
});

// ==================== LANDING PAGE ====================

function showLandingPage() {
    document.getElementById('landing-page').style.display = 'block';
    document.querySelector('.container').style.display = 'none';
    document.querySelector('.navbar').style.display = 'flex';
}

function hideLandingPage() {
    document.getElementById('landing-page').style.display = 'none';
    document.querySelector('.container').style.display = 'block';
}

// ==================== EVENT LISTENERS ====================

function initEventListeners() {
    console.log('Initializing event listeners...');

    // Landing Page CTAs
    const heroGetStarted = document.getElementById('hero-get-started');
    if (heroGetStarted) {
        heroGetStarted.addEventListener('click', () => {
            showAuthModal();
            switchTab('register');
        });
    }

    const heroLearnMore = document.getElementById('hero-learn-more');
    if (heroLearnMore) {
        heroLearnMore.addEventListener('click', () => {
            document.getElementById('features-section').scrollIntoView({ behavior: 'smooth' });
        });
    }

    const ctaGetStarted = document.getElementById('cta-get-started');
    if (ctaGetStarted) {
        ctaGetStarted.addEventListener('click', () => {
            showAuthModal();
            switchTab('register');
        });
    }

    // Wallet Copy Address
    const copyAddressBtn = document.getElementById('copy-address-btn');
    if (copyAddressBtn) {
        copyAddressBtn.addEventListener('click', copyWalletAddress);
    }

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

    // Set event listeners (addEventListener doesn't override inline handlers)
    if (loginBtn) {
        console.log('[EVENT] Login button found, adding event listener');
        loginBtn.addEventListener('click', function(e) {
            console.log('[CLICK] Login button clicked!');
            e.preventDefault();
            e.stopPropagation();
            window.handleLogin();
        });
    } else {
        console.error('[EVENT] Login button NOT found!');
    }

    if (registerBtn) {
        console.log('[EVENT] Register button found, adding event listener');
        registerBtn.addEventListener('click', function(e) {
            console.log('[CLICK] Register button clicked!');
            e.preventDefault();
            e.stopPropagation();
            window.handleRegister();
        });
    } else {
        console.error('[EVENT] Register button NOT found!');
    }
    if (disconnectBtn) disconnectBtn.addEventListener('click', handleDisconnect);
    if (loginRegisterBtn) {
        loginRegisterBtn.addEventListener('click', () => {
            showAuthModal();
            switchTab('login');
        });
    }
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
    const approveUsdcBtn = document.getElementById('approve-usdc-btn');

    if (createWalletBtn) createWalletBtn.addEventListener('click', handleCreateInAppWallet);
    if (connectMetaMaskBtn) connectMetaMaskBtn.addEventListener('click', handleConnectMetaMask);
    if (refreshBalanceBtn) refreshBalanceBtn.addEventListener('click', loadWalletBalance);
    if (exportKeyBtn) exportKeyBtn.addEventListener('click', handleExportPrivateKey);
    if (approveUsdcBtn) approveUsdcBtn.addEventListener('click', handleApproveUSDC);
    
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

// Make functions globally accessible for inline onclick handlers
window.handleLogin = async function() {
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
            showNotification('Login successful!', 'success');

            // Hide landing page and show dashboard
            hideLandingPage();
            hideAuthModal();

            checkWalletAndProceed();
        } else {
            showNotification('Login failed. ' + (data.message || 'Invalid credentials.'), 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed. Please check API server.', 'error');
    }
}

window.handleRegister = async function() {
    console.log('[REGISTER] Button clicked, starting registration process');

    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const passwordConfirm = document.getElementById('register-password-confirm').value;

    console.log('[REGISTER] Email:', email, 'Password length:', password.length);

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
            showNotification('Account created successfully!', 'success');

            // Hide landing page and show dashboard
            hideLandingPage();
            hideAuthModal();

            // If wallet was created during registration, use it immediately
            if (data.wallet && data.wallet.wallet_address) {
                console.log('[REGISTER] Wallet created automatically:', data.wallet.wallet_address);
                hasWallet = true;
                showDashboard();
                // Get full wallet info including balance
                loadWalletBalance();
            } else {
                // Fallback: check wallet status
                checkWalletAndProceed();
            }
        } else {
            showNotification('Registration failed. ' + (data.message || 'Email may already exist.'), 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed. Please check API server.', 'error');
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
            showNotification('Password reset successful! Please login.', 'success');
            // Clear the form
            document.getElementById('reset-email').value = '';
            document.getElementById('reset-new-password').value = '';
            document.getElementById('reset-confirm-password').value = '';
            // Go back to login
            hideForgotPasswordModal();
        } else {
            showNotification('' + (data.message || 'Password reset failed'), 'error');
        }
    } catch (error) {
        console.error('Password reset error:', error);
        showNotification('Password reset failed. Please check API server.', 'error');
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
            showNotification('Creating guest account...', 'info');
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
                showNotification('Failed to create guest account', 'error');
                return;
            }
        }

        showNotification('Creating your wallet...', 'info');

        // Try Safe Wallet first (gasless behind the scenes)
        let response = await fetch(`${API_URL}/wallet/create-safe/${currentUserId}`, {
            method: 'POST'
        });

        let data = await response.json();

        // Fallback to regular EOA wallet if Safe creation fails
        if (!data.success) {
            console.warn('[WALLET] Safe Wallet creation failed, falling back to EOA...');
            showNotification('Creating wallet...', 'info');

            response = await fetch(`${API_URL}/wallet/create-inapp/${currentUserId}`, {
                method: 'POST'
            });

            data = await response.json();
        }

        if (data.success) {
            showNotification('Wallet created successfully!', 'success');
            hasWallet = true;
            showDashboard();
            loadWalletBalance();
        } else {
            showNotification('Failed to create wallet', 'error');
        }
    } catch (error) {
        console.error('Error creating wallet:', error);
        showNotification('Failed to create wallet: ' + error.message, 'error');
    }
}

async function handleConnectMetaMask() {
    if (typeof window.ethereum === 'undefined') {
        showNotification('MetaMask is not installed. Please install it first.', 'error');
        window.open('https://metamask.io/download/', '_blank');
        return;
    }

    try {
        showNotification('🦊 Connecting to MetaMask...', 'info');

        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        const walletAddress = accounts[0];

        // If no user is logged in, create a guest account first
        if (!currentUserId) {
            showNotification('Creating guest account...', 'info');
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
                showNotification('Failed to create guest account', 'error');
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
            showNotification('MetaMask connected successfully!', 'success');
            hasWallet = true;
            showDashboard();
            loadWalletBalance();
        } else {
            showNotification('Failed to connect wallet', 'error');
        }
    } catch (error) {
        console.error('Error connecting MetaMask:', error);
        showNotification('Failed to connect MetaMask: ' + error.message, 'error');
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
    // Validate wallet address exists and is complete (should be 42 chars: 0x + 40 hex)
    if (!wallet.wallet_address || wallet.wallet_address.length < 42) {
        console.error('[WALLET] Invalid wallet address:', wallet.wallet_address);
        showNotification('Invalid wallet address. Please contact support.', 'error');
        return;
    }

    const shortAddress = wallet.wallet_address.slice(0, 6) + '...' + wallet.wallet_address.slice(-4);
    document.getElementById('wallet-address').textContent = shortAddress;

    const walletTypeBadge = document.getElementById('wallet-type-badge');
    if (walletTypeBadge) {
        // Display simple wallet type without technical jargon
        if (wallet.wallet_type === 'safe' || wallet.wallet_type === 'in-app') {
            walletTypeBadge.textContent = 'Your Wallet';
            walletTypeBadge.style.background = '';
        } else if (wallet.wallet_type === 'external' || wallet.wallet_type === 'metamask') {
            walletTypeBadge.textContent = 'Connected Wallet';
            walletTypeBadge.style.background = '';
        } else {
            walletTypeBadge.textContent = 'Wallet';
            walletTypeBadge.style.background = '';
        }
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
        // Allow key export for both in-app and Safe wallets (exports the owner key for Safe)
        if (wallet.wallet_type === 'in-app' || wallet.wallet_type === 'safe') {
            exportKeyBtn.style.display = 'block';
        } else {
            exportKeyBtn.style.display = 'none';
        }
    }

    // Check USDC approval status and show/hide approve button
    checkUSDCApprovalStatus(wallet.wallet_type);
}

//==================== WALLET ADDRESS COPY ====================

async function copyWalletAddress() {
    try {
        const walletAddressElement = document.getElementById('wallet-address-display');
        if (!walletAddressElement) {
            showNotification('Wallet address not found', 'error');
            return;
        }

        const address = walletAddressElement.textContent.trim();

        // Copy to clipboard
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(address);
            showNotification('Wallet address copied!', 'success');

            // Visual feedback - change button text briefly
            const copyBtn = document.getElementById('copy-address-btn');
            if (copyBtn) {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                copyBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';

                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.background = '';
                }, 2000);
            }
        } else {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = address;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showNotification('Wallet address copied!', 'success');
        }
    } catch (error) {
        console.error('Error copying address:', error);
        showNotification('Failed to copy address', 'error');
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
        showNotification('Password required to export private key', 'error');
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
            showPrivateKeyModal(data.private_key, data.wallet_type, data.note);
        } else {
            showNotification('' + (data.message || 'Cannot export private key'), 'error');
        }
    } catch (error) {
        console.error('Error exporting private key:', error);
        showNotification('Failed to export private key', 'error');
    }
}

function showPrivateKeyModal(privateKey, walletType = 'in-app', note = null) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';

    // Add special note for Safe wallets
    const safeWalletNote = walletType === 'safe' ? `
        <p style="color: #3b82f6; margin: 1rem 0; padding: 0.75rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px; border-left: 3px solid #3b82f6;">
            ℹ️ <strong>Safe Wallet:</strong> This is your OWNER key that controls your Safe wallet. Import this key to access and control your Safe.
        </p>
    ` : '';

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <h2 style="color: #ef4444;">🔑 Your Private Key</h2>
            <p style="color: #f59e0b; margin: 1rem 0;">
                ⚠️ KEEP THIS EXTREMELY SAFE! Never share it with anyone!
            </p>
            ${safeWalletNote}

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
        showNotification('Private key copied to clipboard!', 'success');
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

// ==================== USDC APPROVAL (for Trading) ====================

async function checkUSDCApprovalStatus(walletType) {
    if (!currentUserId) return;

    const approveBtn = document.getElementById('approve-usdc-btn');
    if (!approveBtn) return;

    // Only show for in-app wallets
    if (walletType !== 'in-app') {
        approveBtn.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/wallet/usdc-allowance/${currentUserId}`);
        const data = await response.json();

        if (data.success && !data.is_approved) {
            // Show button if USDC is not approved
            approveBtn.style.display = 'block';
            approveBtn.textContent = '✅ Approve';
            approveBtn.disabled = false;
            approveBtn.style.opacity = '1';
        } else if (data.success && data.is_approved) {
            // Show approved status
            approveBtn.style.display = 'block';
            approveBtn.textContent = '✅ Approved';
            approveBtn.disabled = true;
            approveBtn.style.opacity = '0.7';
        } else {
            // Show button by default (assume not approved if can't check)
            approveBtn.style.display = 'block';
            approveBtn.textContent = '✅ Approve';
            approveBtn.disabled = false;
            approveBtn.style.opacity = '1';
        }
    } catch (error) {
        console.error('Error checking USDC approval:', error);
        // Show button on error (better to show than hide)
        approveBtn.style.display = 'block';
        approveBtn.textContent = '✅ Approve';
        approveBtn.disabled = false;
        approveBtn.style.opacity = '1';
    }
}

async function handleApproveUSDC() {
    const approveBtn = document.getElementById('approve-usdc-btn');

    const confirmed = confirm(
        "💰 Approve USDC.e for Trading?\n\n" +
        "This allows Polymarket Exchange to use your USDC.e for trading.\n\n" +
        "• One-time approval (never need to do this again)\n" +
        "• Small gas fee required (~$0.005-0.01 POL)\n" +
        "• Transaction takes 5-30 seconds\n" +
        "• Make sure you have POL for gas fees\n\n" +
        "Click OK to approve."
    );

    if (!confirmed) return;

    try {
        // Show loading state
        approveBtn.disabled = true;
        approveBtn.textContent = '⏳ Approving...';
        showNotification('⏳ Approving USDC.e... This may take up to 30 seconds', 'info');

        const response = await fetch(`${API_URL}/wallet/approve-usdc/${currentUserId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`✅ USDC.e Approved!`, 'success');

            // Update button state
            approveBtn.textContent = '✅ Approved';
            approveBtn.style.opacity = '0.7';

            // Show transaction link in console
            console.log('✅ USDC.e Approval Transaction:', data.explorer_url);

            // Show success modal with transaction details
            showApprovalSuccessModal(data);
        } else {
            // Show detailed error
            const errorMsg = data.error || data.message || 'Unknown error';
            showNotification(`❌ Approval Failed: ${errorMsg}`, 'error');
            approveBtn.disabled = false;
            approveBtn.textContent = '✅ Approve';

            // Show detailed error alert
            alert(`❌ USDC.e Approval Failed\n\n${errorMsg}\n\n` +
                  `Common fixes:\n` +
                  `• Make sure you have at least 0.01 POL for gas (~$0.005)\n` +
                  `• Check that you have USDC.e (not native USDC)\n` +
                  `• Wait a moment and try again\n\n` +
                  `Need help? Check the browser console for details.`);
        }
    } catch (error) {
        console.error('Error approving USDC.e:', error);
        showNotification('Failed to approve USDC.e: ' + error.message, 'error');
        approveBtn.disabled = false;
        approveBtn.textContent = '✅ Approve';

        alert(`❌ Network Error\n\n${error.message}\n\n` +
              `Please check:\n` +
              `• Your internet connection\n` +
              `• Backend server is running\n` +
              `• Try refreshing the page`);
    }
}

function showApprovalSuccessModal(data) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <h2 style="color: #10b981;">✅ USDC Approved!</h2>
            <p style="color: var(--text-secondary); margin: 1rem 0;">
                Your USDC is now approved for trading on Polymarket. You can start trading immediately!
            </p>

            <div style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 10px; margin: 1.5rem 0; border: 1px solid #10b981;">
                <p style="color: var(--text-primary); margin: 0.5rem 0;">
                    <strong>Transaction Hash:</strong><br>
                    <span style="font-family: 'Courier New', monospace; font-size: 0.85rem; word-break: break-all;">${data.tx_hash}</span>
                </p>
                <a href="${data.explorer_url}" target="_blank" rel="noopener noreferrer"
                   style="color: #10b981; text-decoration: none; display: inline-block; margin-top: 0.5rem;">
                    🔗 View on Polygonscan →
                </a>
            </div>

            <div style="background: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 1px solid #3b82f6;">
                <p style="color: var(--text-primary); margin: 0.5rem 0; font-size: 0.9rem;">
                    💡 <strong>What's Next?</strong><br>
                    • You can now place trades on any Polymarket market<br>
                    • You only need to approve once<br>
                    • Future trades will work instantly
                </p>
            </div>

            <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
                <button class="btn btn-primary" id="close-approval-modal">
                    Got it!
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('close-approval-modal').addEventListener('click', () => {
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
    console.log('[AUTH MODAL] Showing auth modal');
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('wallet-modal').style.display = 'none';

    // Log button visibility after modal is shown
    setTimeout(() => {
        const registerBtn = document.getElementById('register-btn');
        const registerForm = document.getElementById('register-form');
        console.log('[AUTH MODAL] Register button element:', registerBtn);
        console.log('[AUTH MODAL] Register form display:', registerForm ? registerForm.style.display : 'not found');
        console.log('[AUTH MODAL] Register button visible:', registerBtn ? window.getComputedStyle(registerBtn).display : 'not found');
    }, 100);
}

function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
}

function switchTab(tab) {
    console.log('[SWITCH TAB] Switching to:', tab);
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.style.display = 'flex';
        registerForm.style.display = 'none';
        console.log('[SWITCH TAB] Now showing login form');
    } else if (tab === 'register') {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.style.display = 'flex';
        loginForm.style.display = 'none';
        console.log('[SWITCH TAB] Now showing register form');
    }

    // Log button state after switch
    setTimeout(() => {
        const registerBtn = document.getElementById('register-btn');
        console.log('[SWITCH TAB] Register button after switch:', registerBtn);
        console.log('[SWITCH TAB] Register button display:', registerBtn ? window.getComputedStyle(registerBtn).display : 'not found');
    }, 50);
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
    div.style.cursor = 'pointer';

    const probability = Math.max(market.yes_price || 0.5, market.no_price || 0.5) * 100;
    const probClass = probability >= 75 ? 'high' : 'medium';

    div.innerHTML = `
        <div class="market-question">${market.question || 'Unknown Market'}</div>
        <div class="market-info">
            <span>Vol: $${((market.volume || 0) / 1000).toFixed(1)}K</span>
            <span class="market-probability ${probClass}">${probability.toFixed(0)}%</span>
        </div>
    `;

    // Add click handler to auto-fill manual trading form
    div.addEventListener('click', () => {
        const manualMarketInput = document.getElementById('manual-market');
        if (manualMarketInput) {
            manualMarketInput.value = market.question || 'Unknown Market';
            // Scroll to manual trading section
            const manualTradingCard = manualMarketInput.closest('.card');
            if (manualTradingCard) {
                manualTradingCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            showNotification('📊 Market loaded to manual trade', 'success');
        }
    });

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
            showNotification('Bot started successfully!', 'success');
        } else {
            showNotification('' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('Failed to start bot', 'error');
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
        showNotification('Settings saved with stop loss and take profit', 'success');
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
        showNotification('Please fill in all fields', 'error');
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
            showNotification('Trade failed', 'error');
        }
    } catch (error) {
        console.error('Error executing trade:', error);
        showNotification('Trade failed', 'error');
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
            showNotification('Insufficient points', 'error');
        }
    } catch (error) {
        console.error('Error redeeming points:', error);
        showNotification('Redemption failed', 'error');
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
            showNotification('Failed to switch network', 'error');
        }
    } catch (error) {
        console.error('Error switching network:', error);
        showNotification('Failed to switch network', 'error');
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
            showNotification('Invalid wallet address format. Must be 42 characters starting with 0x', 'error');
            return;
        }
        targetWallet = manualWallet;
    } else if (selectedTrader) {
        targetWallet = selectedTrader;
    } else {
        showNotification('Please enter a wallet address or select a trader to copy', 'error');
        return;
    }

    if (!copyAmount || copyAmount <= 0) {
        showNotification('Please enter a valid copy amount', 'error');
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
            showNotification('Copy trading started!', 'success');
        } else {
            showNotification('' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error starting copy trading:', error);
        showNotification('Failed to start copy trading', 'error');
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
        showNotification('Failed to stop copy trading', 'error');
    }
}

// ==================== WHALE NOTIFICATIONS ====================

let whaleNotificationQueue = [];
let lastWhaleId = 0;
let currentWhaleNotification = null;
let isShowingWhaleNotification = false;

function showWhaleNotification(whaleData) {
    // Add to queue instead of showing immediately
    whaleNotificationQueue.push(whaleData);

    // Process queue if not already processing
    if (!isShowingWhaleNotification) {
        processWhaleQueue();
    }
}

function processWhaleQueue() {
    // If no notifications in queue or already showing one, stop
    if (whaleNotificationQueue.length === 0 || isShowingWhaleNotification) {
        return;
    }

    // Get next notification from queue
    const whaleData = whaleNotificationQueue.shift();
    isShowingWhaleNotification = true;

    // Display the notification
    displayWhaleNotification(whaleData);
}

function displayWhaleNotification(whaleData) {
    const container = document.getElementById('whale-notifications');
    if (!container) {
        isShowingWhaleNotification = false;
        return;
    }

    const notification = document.createElement('div');
    notification.className = 'whale-notification';
    notification.dataset.whaleId = whaleData.id;
    currentWhaleNotification = notification;

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

    // Auto-dismiss after 8 seconds (reduced for faster queue processing)
    setTimeout(() => {
        dismissWhaleNotification(notification);
    }, 8000);

    container.appendChild(notification);
}

function handleWhaleTradeClick(whaleData) {
    // Fill manual trading form with whale data
    const manualMarketInput = document.getElementById('manual-market');
    const manualPositionSelect = document.getElementById('manual-position');
    const manualAmountInput = document.getElementById('manual-amount');

    if (manualMarketInput) {
        manualMarketInput.value = whaleData.market;
    }

    if (manualPositionSelect) {
        manualPositionSelect.value = whaleData.position;
    }

    if (manualAmountInput) {
        // Suggest a smaller amount than the whale (e.g., 10% of whale amount)
        const suggestedAmount = Math.round(whaleData.amount * 0.1);
        manualAmountInput.value = suggestedAmount;
    }

    // Scroll to manual trading section
    const manualTradingCard = manualMarketInput ? manualMarketInput.closest('.card') : null;
    if (manualTradingCard) {
        manualTradingCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Highlight the section
        manualTradingCard.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)';
        setTimeout(() => {
            manualTradingCard.style.boxShadow = '';
        }, 2000);
    }

    showNotification('🐋 Whale trade loaded! Review and execute.', 'success');
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
        currentWhaleNotification = null;
        isShowingWhaleNotification = false;

        // Process next notification in queue
        setTimeout(() => {
            processWhaleQueue();
        }, 500); // Small delay between notifications
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

console.log('✅ App.js v2.3 - Fixed input field visibility in dark mode');