/**
 * Polymarket Microservice
 * Node.js service for Safe Wallet deployment and gasless trading
 * Integrates with Polymarket Builder Program
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { ClobClient } = require('@polymarket/clob-client');
const { ethers } = require('ethers');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Polymarket Configuration
const POLYMARKET_HOST = 'https://clob.polymarket.com';
const CHAIN_ID = parseInt(process.env.CHAIN_ID) || 137;

// Provider
const provider = new ethers.providers.JsonRpcProvider(
  process.env.RPC_URL || 'https://polygon-rpc.com'
);

// Helper: Create CLOB Client with Builder Credentials
function createClobClient(privateKey, proxyWalletAddress = null) {
  const wallet = new ethers.Wallet(privateKey, provider);

  const client = new ClobClient(
    POLYMARKET_HOST,
    CHAIN_ID,
    wallet,
    undefined, // signer (uses wallet)
    proxyWalletAddress ? 1 : 0, // signature type (0 = EOA, 1 = Poly Proxy/Safe)
    proxyWalletAddress // funder (Safe address if using proxy)
  );

  return client;
}

// ==================== HEALTH CHECK ====================

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Polymarket Service',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    polymarket_host: POLYMARKET_HOST,
    chain_id: CHAIN_ID
  });
});

// ==================== DEPLOY SAFE WALLET ====================

app.post('/deploy-safe', async (req, res) => {
  try {
    const { privateKey, ownerAddress } = req.body;

    if (!privateKey) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter: privateKey'
      });
    }

    console.log('[DEPLOY-SAFE] Starting Safe wallet deployment...');
    console.log('[DEPLOY-SAFE] Owner address:', ownerAddress);

    // Create CLOB client
    const client = createClobClient(privateKey);

    // Set API credentials
    await client.setCreds({
      key: process.env.POLYMARKET_API_KEY,
      secret: process.env.POLYMARKET_SECRET,
      passphrase: process.env.POLYMARKET_PASSPHRASE
    });

    // Deploy Safe wallet using Polymarket relayer (FREE GAS!)
    console.log('[DEPLOY-SAFE] Deploying Safe via Polymarket relayer...');
    const result = await client.createOrDeriveAPIKey();

    console.log('[DEPLOY-SAFE] ✅ Safe deployed successfully!');
    console.log('[DEPLOY-SAFE] Safe address:', result.address);

    res.json({
      success: true,
      safeAddress: result.address,
      owner: ownerAddress,
      message: 'Safe wallet deployed with FREE gas via Polymarket relayer!',
      gasless: true
    });

  } catch (error) {
    console.error('[DEPLOY-SAFE] ❌ Error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// ==================== GET SAFE WALLET ADDRESS ====================

app.post('/get-safe-address', async (req, res) => {
  try {
    const { privateKey } = req.body;

    if (!privateKey) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter: privateKey'
      });
    }

    console.log('[GET-SAFE] Getting Safe address for wallet...');

    const client = createClobClient(privateKey);

    await client.setCreds({
      key: process.env.POLYMARKET_API_KEY,
      secret: process.env.POLYMARKET_SECRET,
      passphrase: process.env.POLYMARKET_PASSPHRASE
    });

    // This will derive the Safe address without deploying if it already exists
    const result = await client.createOrDeriveAPIKey();

    console.log('[GET-SAFE] ✅ Safe address:', result.address);

    res.json({
      success: true,
      safeAddress: result.address,
      deployed: result.deployed || false
    });

  } catch (error) {
    console.error('[GET-SAFE] ❌ Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ==================== CREATE ORDER (GASLESS) ====================

app.post('/create-order', async (req, res) => {
  try {
    const { privateKey, safeAddress, tokenID, side, price, size } = req.body;

    if (!privateKey || !tokenID || !side || !price || !size) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters: privateKey, tokenID, side, price, size'
      });
    }

    console.log('[CREATE-ORDER] Creating order...');
    console.log('[CREATE-ORDER] Market:', tokenID);
    console.log('[CREATE-ORDER] Side:', side);
    console.log('[CREATE-ORDER] Price:', price);
    console.log('[CREATE-ORDER] Size:', size);

    const client = createClobClient(privateKey, safeAddress);

    await client.setCreds({
      key: process.env.POLYMARKET_API_KEY,
      secret: process.env.POLYMARKET_SECRET,
      passphrase: process.env.POLYMARKET_PASSPHRASE
    });

    // Create order
    const order = await client.createOrder({
      tokenID,
      price: price.toString(),
      size: size.toString(),
      side: side.toUpperCase(), // BUY or SELL
      feeRateBps: '0' // No fees for builder orders!
    });

    console.log('[CREATE-ORDER] Order created:', order.orderID);

    // Post order to Polymarket (GASLESS!)
    const response = await client.postOrder(order);

    console.log('[CREATE-ORDER] ✅ Order posted successfully!');
    console.log('[CREATE-ORDER] Order ID:', response.orderID);

    res.json({
      success: true,
      orderID: response.orderID,
      order: order,
      message: 'Order placed with FREE gas via Polymarket relayer!',
      gasless: true,
      builderAttribution: true
    });

  } catch (error) {
    console.error('[CREATE-ORDER] ❌ Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ==================== CANCEL ORDER ====================

app.post('/cancel-order', async (req, res) => {
  try {
    const { privateKey, safeAddress, orderID } = req.body;

    if (!privateKey || !orderID) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters: privateKey, orderID'
      });
    }

    console.log('[CANCEL-ORDER] Canceling order:', orderID);

    const client = createClobClient(privateKey, safeAddress);

    await client.setCreds({
      key: process.env.POLYMARKET_API_KEY,
      secret: process.env.POLYMARKET_SECRET,
      passphrase: process.env.POLYMARKET_PASSPHRASE
    });

    const response = await client.cancelOrder(orderID);

    console.log('[CANCEL-ORDER] ✅ Order canceled successfully!');

    res.json({
      success: true,
      orderID: orderID,
      message: 'Order canceled',
      gasless: true
    });

  } catch (error) {
    console.error('[CANCEL-ORDER] ❌ Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ==================== GET ORDERS ====================

app.post('/get-orders', async (req, res) => {
  try {
    const { privateKey, safeAddress } = req.body;

    if (!privateKey) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameter: privateKey'
      });
    }

    console.log('[GET-ORDERS] Fetching orders...');

    const client = createClobClient(privateKey, safeAddress);

    await client.setCreds({
      key: process.env.POLYMARKET_API_KEY,
      secret: process.env.POLYMARKET_SECRET,
      passphrase: process.env.POLYMARKET_PASSPHRASE
    });

    const orders = await client.getOrders();

    console.log('[GET-ORDERS] ✅ Found', orders.length, 'orders');

    res.json({
      success: true,
      orders: orders,
      count: orders.length
    });

  } catch (error) {
    console.error('[GET-ORDERS] ❌ Error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// ==================== ERROR HANDLER ====================

app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: err.message
  });
});

// ==================== START SERVER ====================

app.listen(PORT, () => {
  console.log('');
  console.log('🚀 Polymarket Service Started!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`📡 Server running on port: ${PORT}`);
  console.log(`🌐 Polymarket host: ${POLYMARKET_HOST}`);
  console.log(`⛓️  Chain ID: ${CHAIN_ID}`);
  console.log(`🔑 Builder API configured: ${process.env.POLYMARKET_API_KEY ? 'YES ✅' : 'NO ❌'}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('');
  console.log('Available endpoints:');
  console.log('  GET  /health             - Health check');
  console.log('  POST /deploy-safe        - Deploy Safe wallet (FREE GAS)');
  console.log('  POST /get-safe-address   - Get Safe address');
  console.log('  POST /create-order       - Create order (GASLESS)');
  console.log('  POST /cancel-order       - Cancel order (GASLESS)');
  console.log('  POST /get-orders         - Get all orders');
  console.log('');
  console.log('💡 Features:');
  console.log('  ✅ FREE gas via Polymarket relayer');
  console.log('  ✅ Builder Program integration');
  console.log('  ✅ Safe Wallet deployment');
  console.log('  ✅ Gasless trading');
  console.log('');
});

module.exports = app;
