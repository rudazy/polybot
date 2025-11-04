# Whale Alert UI Changes

## 🎨 Frontend UI Improvements Required

### Problem
User reported whale alerts need UI improvements:
1. Alerts are too large
2. Not positioned at bottom-right
3. Multiple alerts stack on top of each other

### Required Changes

---

## 1. Make Alerts Smaller

**Current State:** Alerts are likely using default toast/notification size

**Required:** Reduce alert size for less intrusive display

### Implementation Example

```css
/* Whale Alert Component Styles */
.whale-alert {
  max-width: 320px;        /* Reduced from default */
  padding: 12px 16px;      /* Smaller padding */
  font-size: 14px;         /* Smaller text */
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.whale-alert-title {
  font-size: 16px;         /* Smaller heading */
  font-weight: 600;
  margin-bottom: 4px;
}

.whale-alert-amount {
  font-size: 18px;         /* Prominent but not huge */
  font-weight: 700;
  color: #10b981;          /* Green for whale trades */
}

.whale-alert-details {
  font-size: 12px;         /* Small detail text */
  opacity: 0.8;
}
```

---

## 2. Position at Bottom-Right

**Current State:** Alerts may be centered or top-right

**Required:** Fixed position at bottom-right corner

### Implementation Example

```css
/* Whale Alert Container */
.whale-alert-container {
  position: fixed;
  bottom: 24px;            /* Distance from bottom */
  right: 24px;             /* Distance from right */
  z-index: 9999;           /* Above other elements */

  /* Ensure mobile responsiveness */
  @media (max-width: 768px) {
    bottom: 16px;
    right: 16px;
    left: 16px;            /* Full width on mobile */
  }
}
```

### React Component Example

```jsx
// WhaleAlertContainer.jsx
const WhaleAlertContainer = ({ alerts }) => {
  return (
    <div className="whale-alert-container">
      {/* Alerts render here */}
    </div>
  );
};
```

---

## 3. Show One at a Time (Queue System)

**Current State:** Multiple alerts stack/overlap

**Required:** Display one alert at a time with smooth transitions

### Implementation Strategy

**Option A: Simple Queue (Recommended)**
```jsx
import { useState, useEffect } from 'react';

const WhaleAlertManager = () => {
  const [alertQueue, setAlertQueue] = useState([]);
  const [currentAlert, setCurrentAlert] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  // Add new alert to queue
  const addAlert = (alert) => {
    setAlertQueue(prev => [...prev, alert]);
  };

  // Process queue
  useEffect(() => {
    // If no current alert and queue has items
    if (!currentAlert && alertQueue.length > 0) {
      const nextAlert = alertQueue[0];
      setCurrentAlert(nextAlert);
      setAlertQueue(prev => prev.slice(1)); // Remove from queue
      setIsVisible(true);

      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => {
        setIsVisible(false);
        // Wait for fade-out animation
        setTimeout(() => {
          setCurrentAlert(null);
        }, 300);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [currentAlert, alertQueue]);

  return (
    <div className="whale-alert-container">
      {currentAlert && (
        <div
          className={`whale-alert ${isVisible ? 'fade-in' : 'fade-out'}`}
        >
          <div className="whale-alert-title">🐋 Whale Alert</div>
          <div className="whale-alert-amount">
            ${currentAlert.amount.toLocaleString()}
          </div>
          <div className="whale-alert-details">
            {currentAlert.side} on {currentAlert.market}
          </div>
        </div>
      )}
    </div>
  );
};
```

**CSS for Animations:**
```css
.whale-alert {
  transform: translateX(0);
  opacity: 1;
  transition: all 0.3s ease-in-out;
}

.whale-alert.fade-in {
  animation: slideInRight 0.3s ease-out;
}

.whale-alert.fade-out {
  animation: slideOutRight 0.3s ease-in;
}

@keyframes slideInRight {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOutRight {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(400px);
    opacity: 0;
  }
}
```

---

## 4. Complete Example Implementation

### Full React Component

```jsx
// WhaleAlert.jsx
import React, { useState, useEffect } from 'react';
import './WhaleAlert.css';

const WhaleAlert = () => {
  const [alertQueue, setAlertQueue] = useState([]);
  const [currentAlert, setCurrentAlert] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

  // Subscribe to whale trades (WebSocket or polling)
  useEffect(() => {
    const handleWhaleEvent = (event) => {
      const alert = {
        id: Date.now(),
        amount: event.amount,
        side: event.side,
        market: event.market,
        timestamp: new Date()
      };
      setAlertQueue(prev => [...prev, alert]);
    };

    // Example: WebSocket subscription
    // ws.on('whale-trade', handleWhaleEvent);

    // Or polling from API
    const interval = setInterval(async () => {
      const response = await fetch('/api/whale-trades/recent');
      const trades = await response.json();
      // Process new trades...
    }, 10000); // Check every 10 seconds

    return () => {
      clearInterval(interval);
      // ws.off('whale-trade', handleWhaleEvent);
    };
  }, []);

  // Process queue - show one at a time
  useEffect(() => {
    if (!currentAlert && alertQueue.length > 0) {
      const nextAlert = alertQueue[0];
      setCurrentAlert(nextAlert);
      setAlertQueue(prev => prev.slice(1));
      setIsVisible(true);

      // Auto-dismiss after 5 seconds
      const dismissTimer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => {
          setCurrentAlert(null);
        }, 300); // Wait for fade-out
      }, 5000);

      return () => clearTimeout(dismissTimer);
    }
  }, [currentAlert, alertQueue]);

  if (!currentAlert) return null;

  return (
    <div className="whale-alert-container">
      <div className={`whale-alert ${isVisible ? 'fade-in' : 'fade-out'}`}>
        <div className="whale-alert-icon">🐋</div>
        <div className="whale-alert-content">
          <div className="whale-alert-title">Whale Alert</div>
          <div className="whale-alert-amount">
            ${currentAlert.amount.toLocaleString()}
          </div>
          <div className="whale-alert-details">
            <span className={`side ${currentAlert.side.toLowerCase()}`}>
              {currentAlert.side}
            </span>
            {' '}on {currentAlert.market}
          </div>
        </div>
        <button
          className="whale-alert-close"
          onClick={() => setIsVisible(false)}
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default WhaleAlert;
```

### Full CSS Styles

```css
/* WhaleAlert.css */

.whale-alert-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  pointer-events: none; /* Allow clicking through empty space */
}

.whale-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 320px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  pointer-events: auto; /* Alert itself is clickable */
  backdrop-filter: blur(10px);
}

.whale-alert-icon {
  font-size: 28px;
  flex-shrink: 0;
  filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.3));
}

.whale-alert-content {
  flex: 1;
  min-width: 0; /* Allow text truncation */
}

.whale-alert-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.whale-alert-amount {
  font-size: 20px;
  font-weight: 700;
  color: #10b981; /* Green */
  margin-bottom: 4px;
  font-variant-numeric: tabular-nums;
}

.whale-alert-details {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.whale-alert-details .side {
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  font-size: 11px;
}

.whale-alert-details .side.buy,
.whale-alert-details .side.yes {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.whale-alert-details .side.sell,
.whale-alert-details .side.no {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.whale-alert-close {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.whale-alert-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
}

/* Animations */
.whale-alert.fade-in {
  animation: slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.whale-alert.fade-out {
  animation: slideOutRight 0.3s cubic-bezier(0.7, 0, 0.84, 0);
}

@keyframes slideInRight {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOutRight {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(400px);
    opacity: 0;
  }
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .whale-alert-container {
    bottom: 16px;
    right: 16px;
    left: 16px;
  }

  .whale-alert {
    max-width: 100%;
  }

  @keyframes slideInRight {
    from {
      transform: translateY(100px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideOutRight {
    from {
      transform: translateY(0);
      opacity: 1;
    }
    to {
      transform: translateY(100px);
      opacity: 0;
    }
  }
}

/* Dark mode support */
@media (prefers-color-scheme: light) {
  .whale-alert {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow:
      0 4px 16px rgba(0, 0, 0, 0.1),
      0 0 0 1px rgba(0, 0, 0, 0.05);
  }

  .whale-alert-title {
    color: rgba(0, 0, 0, 0.7);
  }

  .whale-alert-details {
    color: rgba(0, 0, 0, 0.6);
  }

  .whale-alert-close {
    color: rgba(0, 0, 0, 0.5);
  }

  .whale-alert-close:hover {
    background: rgba(0, 0, 0, 0.05);
    color: rgba(0, 0, 0, 0.9);
  }
}
```

---

## 5. Testing Checklist

- [ ] Alert appears at bottom-right corner
- [ ] Alert size is appropriately small (not intrusive)
- [ ] Only one alert visible at a time
- [ ] Multiple alerts queue properly
- [ ] Alert auto-dismisses after 5 seconds
- [ ] Smooth slide-in animation from right
- [ ] Smooth slide-out animation to right
- [ ] Close button works
- [ ] Mobile responsive (bottom center on mobile)
- [ ] Doesn't block important UI elements
- [ ] Queue processes correctly (FIFO)
- [ ] No alerts stack on top of each other

---

## 6. Configuration Options

Add these to your whale alert configuration:

```javascript
const WHALE_ALERT_CONFIG = {
  // Minimum trade size to trigger alert
  minTradeSize: 10000, // $10,000

  // Display duration
  displayDuration: 5000, // 5 seconds

  // Max queue size (prevent overflow)
  maxQueueSize: 10,

  // Animation duration
  animationDuration: 300, // ms

  // Position
  position: {
    bottom: 24,
    right: 24,
  },

  // Size
  maxWidth: 320, // px
};
```

---

## 7. Integration with Existing Code

If you already have a whale alert component, modify it to:

1. **Add queue state:**
   ```jsx
   const [alertQueue, setAlertQueue] = useState([]);
   const [currentAlert, setCurrentAlert] = useState(null);
   ```

2. **Update CSS positioning:**
   ```css
   position: fixed;
   bottom: 24px;
   right: 24px;
   ```

3. **Reduce size:**
   ```css
   max-width: 320px;
   padding: 12px 16px;
   font-size: 14px;
   ```

4. **Add queue logic:**
   ```jsx
   // Only show one alert at a time
   if (!currentAlert && alertQueue.length > 0) {
     setCurrentAlert(alertQueue[0]);
     setAlertQueue(prev => prev.slice(1));
   }
   ```

---

## 8. Alternative: Using Toast Library

If using a toast library (react-hot-toast, react-toastify), configure it:

```jsx
import toast, { Toaster } from 'react-hot-toast';

// Configure toaster
<Toaster
  position="bottom-right"
  toastOptions={{
    duration: 5000,
    style: {
      maxWidth: '320px',
      padding: '12px 16px',
    },
  }}
/>

// Show whale alert
toast.custom((t) => (
  <div className="whale-alert">
    🐋 Whale Alert: ${amount.toLocaleString()}
  </div>
), {
  duration: 5000,
  position: 'bottom-right',
});
```

---

## Summary

**Changes Required:**
1. ✅ Reduce alert size to max-width: 320px
2. ✅ Position at bottom-right (fixed position)
3. ✅ Implement queue system (one alert at a time)
4. ✅ Add smooth animations (slide in/out)
5. ✅ Auto-dismiss after 5 seconds
6. ✅ Mobile responsive

**Files to Modify:**
- WhaleAlert component (or similar)
- WhaleAlert.css (or styled-components)
- Add queue state management

**Expected Result:**
Small, non-intrusive alerts that appear at bottom-right, display one at a time with smooth animations, and auto-dismiss.
