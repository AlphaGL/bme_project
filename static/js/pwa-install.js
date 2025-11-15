// SIMPLIFIED PWA Installation - GUARANTEED TO WORK
// Save as: static/js/pwa-install.js

let deferredPrompt = null;
let installNotification = null;

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  console.log('[PWA] Starting initialization...');
  
  // Register service worker FIRST
  if ('serviceWorker' in navigator) {
    registerServiceWorker();
  }

  // Create notification element
  createInstallNotification();

  // CRITICAL: Listen for beforeinstallprompt
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] ✅ beforeinstallprompt fired!');
    e.preventDefault(); // Prevent default mini-infobar
    deferredPrompt = e; // Store the event
    
    // Show our custom install button
    showInstallNotification();
  });

  // Listen for successful install
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] ✅ App installed!');
    hideInstallNotification();
    deferredPrompt = null;
    showToast('success', '✅ Installed!', 'App installed successfully!');
  });

  // Check if already installed
  if (isStandalone()) {
    console.log('[PWA] Already installed');
    hideInstallNotification();
  }
}

async function registerServiceWorker() {
  try {
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/'
    });
    
    console.log('[PWA] ✅ Service Worker registered:', registration.scope);
    
    // Check for updates
    registration.update();
    
  } catch (error) {
    console.error('[PWA] ❌ Service Worker failed:', error);
  }
}

function createInstallNotification() {
  const existing = document.getElementById('pwa-install-banner');
  if (existing) existing.remove();

  installNotification = document.createElement('div');
  installNotification.id = 'pwa-install-banner';
  installNotification.style.cssText = `
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #8B1538, #6B0F28);
    color: white;
    padding: 15px 20px;
    z-index: 9999;
    display: none;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    border-bottom: 3px solid #D4AF37;
  `;
  
  installNotification.innerHTML = `
    <div style="display: flex; align-items: center; gap: 15px; max-width: 1200px; margin: 0 auto;">
      <i class="fas fa-mobile-alt" style="font-size: 2rem; color: #D4AF37;"></i>
      <div style="flex: 1;">
        <h6 style="margin: 0 0 4px 0; font-size: 1rem; font-weight: 700;">Install FUTO BME App</h6>
        <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">Quick access & offline mode</p>
      </div>
      <button id="pwa-install-btn" style="
        background: #D4AF37;
        border: none;
        color: #000;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: 600;
        cursor: pointer;
        font-size: 0.9rem;
        white-space: nowrap;
      ">
        <i class="fas fa-download"></i> Install
      </button>
      <button id="pwa-close-btn" style="
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 1.2rem;
        padding: 5px 10px;
      ">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;
  
  document.body.appendChild(installNotification);
  
  // Add click handlers
  document.getElementById('pwa-install-btn').addEventListener('click', handleInstall);
  document.getElementById('pwa-close-btn').addEventListener('click', () => {
    hideInstallNotification();
    localStorage.setItem('pwa-dismissed', Date.now());
  });
}

function showInstallNotification() {
  // Check if dismissed recently (within 24 hours)
  const dismissed = localStorage.getItem('pwa-dismissed');
  if (dismissed) {
    const hours = (Date.now() - parseInt(dismissed)) / (1000 * 60 * 60);
    if (hours < 24) {
      console.log('[PWA] Banner dismissed recently');
      return;
    }
  }
  
  if (installNotification && deferredPrompt) {
    console.log('[PWA] Showing install banner');
    installNotification.style.display = 'block';
  }
}

function hideInstallNotification() {
  if (installNotification) {
    installNotification.style.display = 'none';
  }
}

async function handleInstall() {
  console.log('[PWA] Install button clicked');
  
  if (!deferredPrompt) {
    console.log('[PWA] No prompt available');
    showInstallInstructions();
    return;
  }

  const installBtn = document.getElementById('pwa-install-btn');
  installBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Installing...';
  installBtn.disabled = true;

  try {
    // Show the install prompt
    console.log('[PWA] Calling prompt()...');
    await deferredPrompt.prompt();
    
    // Wait for user's response
    const result = await deferredPrompt.userChoice;
    console.log('[PWA] User choice:', result.outcome);
    
    if (result.outcome === 'accepted') {
      console.log('[PWA] ✅ User accepted!');
      hideInstallNotification();
      showToast('success', 'Installing...', 'Please wait while we install the app');
    } else {
      console.log('[PWA] ❌ User declined');
      installBtn.innerHTML = '<i class="fas fa-download"></i> Install';
      installBtn.disabled = false;
    }
    
  } catch (error) {
    console.error('[PWA] ❌ Install error:', error);
    installBtn.innerHTML = '<i class="fas fa-download"></i> Install';
    installBtn.disabled = false;
    showToast('error', 'Failed', error.message);
  }
  
  deferredPrompt = null;
}

function showInstallInstructions() {
  const ua = navigator.userAgent.toLowerCase();
  let message = '';
  
  if (/iphone|ipad|ipod/.test(ua)) {
    if (/safari/.test(ua) && !/chrome/.test(ua)) {
      message = '1. Tap the Share button (square with arrow)<br>2. Scroll and tap "Add to Home Screen"<br>3. Tap "Add"';
    } else {
      message = 'Please open this site in Safari to install';
    }
  } else if (/android/.test(ua)) {
    message = 'Look for "Install app" or "Add to Home screen" in your browser menu (⋮)';
  } else {
    message = 'Installation is available in Chrome, Edge, or Safari on mobile';
  }
  
  showToast('info', 'How to Install', message, 8000);
}

function isStandalone() {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  );
}

function showToast(type, title, message, duration = 4000) {
  const icons = {
    success: 'fa-check-circle',
    error: 'fa-times-circle',
    warning: 'fa-exclamation-triangle',
    info: 'fa-info-circle'
  };
  
  const colors = {
    success: '#198754',
    error: '#dc3545',
    warning: '#ffc107',
    info: '#0dcaf0'
  };
  
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: white;
    color: #333;
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    z-index: 10000;
    max-width: 350px;
    border-left: 4px solid ${colors[type]};
    animation: slideIn 0.3s ease;
  `;
  
  toast.innerHTML = `
    <div style="display: flex; align-items: start; gap: 10px;">
      <i class="fas ${icons[type]}" style="color: ${colors[type]}; font-size: 1.2rem; margin-top: 2px;"></i>
      <div style="flex: 1;">
        <strong style="display: block; margin-bottom: 4px;">${title}</strong>
        <div style="font-size: 0.9rem; color: #666;">${message}</div>
      </div>
      <button onclick="this.parentElement.parentElement.remove()" style="
        background: none;
        border: none;
        font-size: 1.2rem;
        color: #999;
        cursor: pointer;
        padding: 0;
        line-height: 1;
      ">&times;</button>
    </div>
  `;
  
  document.body.appendChild(toast);
  
  if (duration > 0) {
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

// Add CSS animations
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

console.log('[PWA] Script loaded ✅');