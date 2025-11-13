// PWA Installation Handler for FUTO BME Portal

let deferredPrompt;
let installButton;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initializePWA();
});

function initializePWA() {
  // Register service worker
  if ('serviceWorker' in navigator) {
    registerServiceWorker();
  }

  // Create install button
  createInstallButton();

  // Listen for beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] beforeinstallprompt event fired');
    e.preventDefault();
    deferredPrompt = e;
    showInstallButton();
  });

  // Listen for app installed event
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    hideInstallButton();
    showInstallSuccessMessage();
  });

  // Check if already installed
  if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    console.log('[PWA] App is running in standalone mode');
    hideInstallButton();
  }
}

async function registerServiceWorker() {
  try {
    const registration = await navigator.serviceWorker.register('/static/js/service-worker.js', {
      scope: '/'
    });
    
    console.log('[PWA] Service Worker registered:', registration.scope);

    // Check for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New service worker available
          showUpdateNotification();
        }
      });
    });
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

function createInstallButton() {
  // Create floating install button
  installButton = document.createElement('button');
  installButton.id = 'pwa-install-button';
  installButton.innerHTML = `
    <i class="fas fa-download me-2"></i>
    <span class="install-text">Install App</span>
  `;
  installButton.className = 'btn btn-primary pwa-install-btn';
  installButton.style.display = 'none';
  
  installButton.addEventListener('click', installApp);
  
  document.body.appendChild(installButton);
}

function showInstallButton() {
  if (installButton) {
    installButton.style.display = 'flex';
    // Animate in
    setTimeout(() => {
      installButton.classList.add('show');
    }, 100);
  }
}

function hideInstallButton() {
  if (installButton) {
    installButton.classList.remove('show');
    setTimeout(() => {
      installButton.style.display = 'none';
    }, 300);
  }
}

async function installApp() {
  if (!deferredPrompt) {
    console.log('[PWA] Install prompt not available');
    return;
  }

  // Show install prompt
  deferredPrompt.prompt();

  // Wait for user choice
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`[PWA] User response: ${outcome}`);

  if (outcome === 'accepted') {
    console.log('[PWA] User accepted the install prompt');
  } else {
    console.log('[PWA] User dismissed the install prompt');
  }

  // Clear the deferred prompt
  deferredPrompt = null;
  hideInstallButton();
}

function showInstallSuccessMessage() {
  // Create success notification
  const notification = document.createElement('div');
  notification.className = 'alert alert-success pwa-notification';
  notification.innerHTML = `
    <i class="fas fa-check-circle me-2"></i>
    <strong>Success!</strong> FUTO BME Portal has been installed on your device.
  `;
  
  document.body.appendChild(notification);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 500);
  }, 5000);
}

function showUpdateNotification() {
  // Create update notification
  const notification = document.createElement('div');
  notification.className = 'alert alert-info pwa-notification';
  notification.innerHTML = `
    <i class="fas fa-sync-alt me-2"></i>
    <strong>Update Available!</strong> 
    <button class="btn btn-sm btn-light ms-2" onclick="updateServiceWorker()">Update Now</button>
  `;
  
  document.body.appendChild(notification);
}

function updateServiceWorker() {
  navigator.serviceWorker.getRegistration().then((registration) => {
    if (registration && registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  });
}

// Detect when app goes offline/online
window.addEventListener('online', () => {
  showNetworkStatus('online');
});

window.addEventListener('offline', () => {
  showNetworkStatus('offline');
});

function showNetworkStatus(status) {
  const notification = document.createElement('div');
  notification.className = `alert pwa-notification ${status === 'online' ? 'alert-success' : 'alert-warning'}`;
  notification.innerHTML = status === 'online' 
    ? '<i class="fas fa-wifi me-2"></i>Back online!' 
    : '<i class="fas fa-wifi-slash me-2"></i>No internet connection';
  
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 500);
  }, 3000);
}

// Add to home screen prompt for iOS
function showiOSInstallPrompt() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  const isInStandaloneMode = window.navigator.standalone === true;

  if (isIOS && !isInStandaloneMode) {
    const iosPrompt = document.createElement('div');
    iosPrompt.className = 'ios-install-prompt';
    iosPrompt.innerHTML = `
      <div class="ios-prompt-content">
        <button class="ios-close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
        <h5>Install FUTO BME Portal</h5>
        <p>Tap <i class="fas fa-share"></i> then "Add to Home Screen"</p>
      </div>
    `;
    document.body.appendChild(iosPrompt);

    setTimeout(() => {
      iosPrompt.classList.add('show');
    }, 1000);
  }
}

// Show iOS prompt after a delay
setTimeout(showiOSInstallPrompt, 3000);