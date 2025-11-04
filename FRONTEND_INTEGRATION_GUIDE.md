# Frontend Integration Guide - USDC Approval Button

## 🎯 What You Need to Add

Add a small **"Approve USDC"** button next to the "Export Wallet" button in your wallet UI.

---

## 📍 Where to Add the Button

**Location:** In your wallet dashboard/settings page, near the "Export Private Key" button

**Layout Example:**
```
┌─────────────────────────────────────┐
│  Your Wallet                         │
│  0x1234...5678                       │
│                                      │
│  Balance: 100.50 USDC               │
│  Balance: 0.5 POL                   │
│                                      │
│  [Export Private Key]  [Approve USDC for Trading]  │
│   ↑ Existing button     ↑ NEW BUTTON (small)        │
└─────────────────────────────────────┘
```

---

## 🔧 Frontend Implementation

### Step 1: Add State Management

```jsx
// In your Wallet component
import { useState, useEffect } from 'react';

const WalletComponent = ({ userId }) => {
  const [isApproved, setIsApproved] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isCheckingApproval, setIsCheckingApproval] = useState(true);

  // Check approval status on mount
  useEffect(() => {
    checkApprovalStatus();
  }, [userId]);

  const checkApprovalStatus = async () => {
    try {
      setIsCheckingApproval(true);
      const response = await fetch(
        `https://polymarket-bot-api-production.up.railway.app/wallet/usdc-allowance/${userId}`
      );
      const data = await response.json();

      if (data.success) {
        setIsApproved(data.is_approved);
      }
    } catch (error) {
      console.error('Error checking approval:', error);
    } finally {
      setIsCheckingApproval(false);
    }
  };

  const handleApproveUSDC = async () => {
    try {
      setIsApproving(true);

      const response = await fetch(
        `https://polymarket-bot-api-production.up.railway.app/wallet/approve-usdc/${userId}`,
        { method: 'POST' }
      );

      const data = await response.json();

      if (data.success) {
        alert(`✅ USDC Approved!\n\nTransaction: ${data.tx_hash}\n\nYou can now trade on Polymarket!`);
        setIsApproved(true);
      } else {
        alert(`❌ Approval Failed\n\n${data.message}\n\n${data.explanation || ''}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="wallet-container">
      {/* Your existing wallet UI */}

      <div className="wallet-actions">
        {/* Existing export button */}
        <button className="btn-secondary" onClick={handleExportKey}>
          Export Private Key
        </button>

        {/* NEW: Approval button */}
        {!isApproved ? (
          <button
            className="btn-approve-usdc"
            onClick={handleApproveUSDC}
            disabled={isApproving}
            title="Required before first trade"
          >
            {isApproving ? (
              <>⏳ Approving...</>
            ) : (
              <>✅ Approve USDC</>
            )}
          </button>
        ) : (
          <span className="approval-status">
            ✅ USDC Approved for Trading
          </span>
        )}
      </div>
    </div>
  );
};
```

---

## 🎨 CSS Styling (Small Button)

```css
/* Approval button - small and compact */
.btn-approve-usdc {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 8px 16px;  /* Smaller padding */
  border-radius: 6px;
  font-size: 13px;    /* Smaller text */
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  margin-left: 8px;   /* Space from export button */
}

.btn-approve-usdc:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-approve-usdc:disabled {
  background: #6b7280;
  cursor: not-allowed;
  transform: none;
}

.approval-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-left: 8px;
}

/* Make buttons side by side */
.wallet-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
```

---

## 🔄 Before Trading Flow

**Important:** Check approval status before allowing trades!

```jsx
// In your Trading component
const TradingComponent = ({ userId }) => {
  const [isApproved, setIsApproved] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    checkIfApproved();
  }, [userId]);

  const checkIfApproved = async () => {
    try {
      const response = await fetch(
        `https://polymarket-bot-api-production.up.railway.app/wallet/usdc-allowance/${userId}`
      );
      const data = await response.json();

      if (data.success) {
        setIsApproved(data.is_approved);
      }
    } catch (error) {
      console.error('Error checking approval:', error);
    } finally {
      setIsChecking(false);
    }
  };

  const handleTrade = async () => {
    // Check approval first
    if (!isApproved) {
      alert('⚠️ Please approve USDC first!\n\nGo to your wallet and click "Approve USDC for Trading"');
      return;
    }

    // Proceed with trade...
  };

  return (
    <div>
      {!isApproved && (
        <div className="warning-banner">
          ⚠️ You need to approve USDC before trading.
          <a href="/wallet">Go to Wallet</a>
        </div>
      )}

      {/* Trading form */}
    </div>
  );
};
```

---

## 📋 Complete Implementation Checklist

### 1. Wallet Page Changes
- [ ] Add approval status check on page load
- [ ] Add "Approve USDC" button next to export button
- [ ] Make button small (13px font, 8px padding)
- [ ] Show loading state while approving
- [ ] Show success message with transaction hash
- [ ] Change button to "✅ USDC Approved" after success

### 2. Trading Page Changes
- [ ] Check approval status before showing trade form
- [ ] Show warning banner if not approved
- [ ] Prevent trade if not approved
- [ ] Add link to wallet page from warning

### 3. User Experience
- [ ] Show approval button only for in-app wallets
- [ ] For external wallets, show: "You'll approve USDC when you make your first trade"
- [ ] Add tooltip on approval button: "Required before first trade"
- [ ] Show transaction link after approval

---

## 🧪 Testing Steps

1. **Register new user** → Should see "Approve USDC" button
2. **Click approve button** → Should show loading state
3. **Wait 10-30 seconds** → Should show success message
4. **Refresh page** → Button should change to "✅ USDC Approved"
5. **Try to trade** → Should work now!

---

## 📱 Mobile Responsive

```css
@media (max-width: 768px) {
  .wallet-actions {
    flex-direction: column;
    width: 100%;
  }

  .btn-approve-usdc,
  .approval-status {
    width: 100%;
    margin-left: 0;
    margin-top: 8px;
  }
}
```

---

## 🎯 User Flow Diagram

```
User registers
  ↓
Creates/connects wallet
  ↓
Goes to wallet page → Sees "Approve USDC" button
  ↓
Clicks approve → Loading for 10-30 seconds
  ↓
✅ Success message + transaction link
  ↓
Button changes to "✅ USDC Approved"
  ↓
User can now trade!
```

---

## 🔗 API Endpoints Summary

**Check Approval:**
```javascript
GET https://polymarket-bot-api-production.up.railway.app/wallet/usdc-allowance/{userId}

Response:
{
  "success": true,
  "is_approved": false,  // ← Check this
  "allowance": 0
}
```

**Approve USDC:**
```javascript
POST https://polymarket-bot-api-production.up.railway.app/wallet/approve-usdc/{userId}

Response:
{
  "success": true,
  "message": "USDC approved for Polymarket trading!",
  "tx_hash": "0xabcd...",
  "explorer_url": "https://polygonscan.com/tx/0xabcd..."
}
```

---

## ⚠️ Important Notes

1. **Gas Fees:** Users need ~$0.01-0.05 worth of POL for approval transaction
2. **One-Time:** Approval is permanent - only needed once per wallet
3. **External Wallets:** Show different message - they approve via wallet popup
4. **Transaction Time:** Takes 5-30 seconds on Polygon network
5. **Error Handling:** Show clear error if insufficient POL for gas

---

## 🎨 Alternative: Compact Icon Button

If you want a smaller icon-only button:

```jsx
<button
  className="btn-icon-approve"
  onClick={handleApproveUSDC}
  title="Approve USDC for Trading"
>
  {isApproved ? '✅' : '🔓'}
</button>
```

```css
.btn-icon-approve {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 16px;
  padding: 0;
  /* Add other styles */
}
```

---

## 🐛 Troubleshooting

**Q: Button shows but clicking does nothing**
- Check browser console for errors
- Verify userId is correct
- Check network tab for API response

**Q: "User not found" error**
- User needs to be registered first
- Check if userId is valid

**Q: Approval succeeds but trading still fails**
- Wait 30 seconds for blockchain confirmation
- Refresh the page
- Check approval status API

**Q: "External wallet detected" message**
- Normal for Rabby/MetaMask wallets
- They approve automatically during first trade
- No need to show approval button

---

## 🚀 Quick Copy-Paste Solution

**Minimal implementation** (if you just want it working quickly):

```jsx
// Add to your Wallet component
const [needsApproval, setNeedsApproval] = useState(false);

useEffect(() => {
  // Check on mount
  fetch(`https://polymarket-bot-api-production.up.railway.app/wallet/usdc-allowance/${userId}`)
    .then(res => res.json())
    .then(data => setNeedsApproval(!data.is_approved));
}, []);

const approve = async () => {
  if (!confirm('Approve USDC for trading? (~$0.01 gas fee)')) return;

  const res = await fetch(
    `https://polymarket-bot-api-production.up.railway.app/wallet/approve-usdc/${userId}`,
    { method: 'POST' }
  );
  const data = await res.json();

  if (data.success) {
    alert('✅ Approved! You can now trade.');
    setNeedsApproval(false);
  } else {
    alert('❌ ' + data.message);
  }
};

// In your JSX, next to export button:
{needsApproval && (
  <button onClick={approve} style={{fontSize: '13px', padding: '8px 16px'}}>
    ✅ Approve USDC
  </button>
)}
```

---

That's it! Once you add this button to your frontend, users will be able to approve USDC and trade successfully! 🎉
