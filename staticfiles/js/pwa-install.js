// Enhanced PWA Installation Handler for FUTO BME Portal

let deferredPrompt;
let installButton;
let installBanner;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initializePWA();
});

function initializePWA() {
  // Register service worker
  if ('serviceWorker' in navigator) {
    registerServiceWorker();
  }

  // Create install UI elements
  createInstallButton();
  createInstallBanner();

  // Listen for beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] beforeinstallprompt event fired');
    e.preventDefault();
    deferredPrompt = e;
    showInstallPrompt();
  });

  // Listen for app installed event
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    hideInstallPrompt();
    showInstallSuccessMessage();
  });

  // Check if already installed
  if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    console.log('[PWA] App is running in standalone mode');
    hideInstallPrompt();
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
          showUpdateNotification();
        }
      });
    });
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

function createInstallButton() {
  // Create enhanced floating install button
  installButton = document.createElement('button');
  installButton.id = 'pwa-install-button';
  installButton.className = 'btn pwa-install-btn';
  installButton.setAttribute('aria-label', 'Install FUTO BME App');
  installButton.innerHTML = `
    <div class="install-icon">
      <i class="fas fa-mobile-alt"></i>
    </div>
    <div class="install-text">Install App</div>
    <div class="install-subtitle">Access Offline</div>
  `;
  installButton.style.display = 'none';
  
  installButton.addEventListener('click', installApp);
  
  document.body.appendChild(installButton);
}

function createInstallBanner() {
  // Create top banner for install prompt (alternative UI)
  installBanner = document.createElement('div');
  installBanner.id = 'pwa-install-banner';
  installBanner.className = 'pwa-install-banner';
  installBanner.innerHTML = `
    <div class="pwa-install-banner-content">
      <div class="pwa-install-banner-icon">
        <i class="fas fa-mobile-alt"></i>
      </div>
      <div class="pwa-install-banner-text">
        <h5>Install FUTO BME Portal</h5>
        <p>Get quick access and work offline</p>
      </div>
    </div>
    <div class="pwa-install-banner-actions">
      <button class="pwa-install-banner-btn" onclick="installApp()">
        <i class="fas fa-download me-1"></i>Install
      </button>
      <button class="pwa-install-banner-btn dismiss" onclick="dismissInstallBanner()">
        Later
      </button>
    </div>
  `;
  installBanner.style.display = 'none';
  
  document.body.insertBefore(installBanner, document.body.firstChild);
}

function showInstallPrompt() {
  // Check if user has dismissed install prompt recently
  const dismissed = localStorage.getItem('pwa-install-dismissed');
  const dismissedTime = localStorage.getItem('pwa-install-dismissed-time');
  
  if (dismissed === 'true' && dismissedTime) {
    const hoursSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60);
    if (hoursSinceDismissed < 24) {
      // Don't show for 24 hours after dismissal
      console.log('[PWA] Install prompt dismissed recently');
      return;
    }
  }
  
  // Show button
  showInstallButton();
  
  // Show banner after 5 seconds (less intrusive)
  setTimeout(() => {
    if (deferredPrompt && !isAppInstalled()) {
      showInstallBanner();
    }
  }, 5000);
}

function showInstallButton() {
  if (installButton) {
    installButton.style.display = 'flex';
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

function showInstallBanner() {
  if (installBanner) {
    installBanner.style.display = 'flex';
    setTimeout(() => {
      installBanner.classList.add('show');
    }, 100);
  }
}

function hideInstallBanner() {
  if (installBanner) {
    installBanner.classList.remove('show');
    setTimeout(() => {
      installBanner.style.display = 'none';
    }, 300);
  }
}

function dismissInstallBanner() {
  hideInstallBanner();
  // Remember dismissal for 24 hours
  localStorage.setItem('pwa-install-dismissed', 'true');
  localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
}

function hideInstallPrompt() {
  hideInstallButton();
  hideInstallBanner();
}

async function installApp() {
  if (!deferredPrompt) {
    console.log('[PWA] Install prompt not available');
    showInstallInstructions();
    return;
  }

  // Hide UI
  hideInstallPrompt();

  // Show install prompt
  deferredPrompt.prompt();

  // Wait for user choice
  const { outcome } = await deferredPrompt.userChoice;
  console.log(`[PWA] User response: ${outcome}`);

  if (outcome === 'accepted') {
    console.log('[PWA] User accepted the install prompt');
    showInstallSuccessMessage();
  } else {
    console.log('[PWA] User dismissed the install prompt');
    // Show button again after dismissal
    setTimeout(() => {
      showInstallButton();
    }, 60000); // Show again after 1 minute
  }

  // Clear the deferred prompt
  deferredPrompt = null;
}

function isAppInstalled() {
  // Check if app is installed
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.navigator.standalone === true;
}

function showInstallInstructions() {
  // Show manual install instructions for browsers that don't support prompt
  const notification = document.createElement('div');
  notification.className = 'alert alert-info pwa-notification';
  
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  
  if (isIOS) {
    notification.innerHTML = `
      <i class="fas fa-info-circle me-2"></i>
      <div>
        <strong>Install FUTO BME App</strong><br>
        Tap <i class="fas fa-share"></i> then "Add to Home Screen"
      </div>
    `;
  } else {
    notification.innerHTML = `
      <i class="fas fa-info-circle me-2"></i>
      <div>
        <strong>Install Instructions</strong><br>
        Look for the install icon in your browser's menu or address bar
      </div>
    `;
  }
  
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 500);
  }, 8000);
}

function showInstallSuccessMessage() {
  const notification = document.createElement('div');
  notification.className = 'alert alert-success pwa-notification';
  notification.innerHTML = `
    <i class="fas fa-check-circle me-2"></i>
    <div>
      <strong>Success!</strong><br>
      FUTO BME Portal installed on your device
    </div>
  `;
  
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 500);
  }, 5000);
}

function showUpdateNotification() {
  const notification = document.createElement('div');
  notification.className = 'alert alert-info pwa-notification';
  notification.innerHTML = `
    <i class="fas fa-sync-alt me-2"></i>
    <div>
      <strong>Update Available!</strong><br>
      <button class="btn btn-sm btn-light mt-2" onclick="updateServiceWorker()">
        Update Now
      </button>
    </div>
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

// Network status notifications
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
    : '<i class="fas fa-wifi-slash me-2"></i>No internet connection - Working offline';
  
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 500);
  }, 3000);
}

// iOS-specific install prompt
function showiOSInstallPrompt() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  const isInStandaloneMode = window.navigator.standalone === true;

  if (isIOS && !isInStandaloneMode) {
    // Check if dismissed recently
    const dismissed = localStorage.getItem('ios-prompt-dismissed');
    const dismissedTime = localStorage.getItem('ios-prompt-dismissed-time');
    
    if (dismissed === 'true' && dismissedTime) {
      const hoursSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60);
      if (hoursSinceDismissed < 72) { // Don't show for 3 days
        return;
      }
    }
    
    const iosPrompt = document.createElement('div');
    iosPrompt.className = 'ios-install-prompt';
    iosPrompt.innerHTML = `
      <div class="ios-prompt-content">
        <button class="ios-close-btn" onclick="dismissiOSPrompt()">×</button>
        <div class="mb-2">
          <i class="fas fa-mobile-alt" style="font-size: 2rem; color: #D4AF37;"></i>
        </div>
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

function dismissiOSPrompt() {
  const iosPrompt = document.querySelector('.ios-install-prompt');
  if (iosPrompt) {
    iosPrompt.classList.remove('show');
    setTimeout(() => iosPrompt.remove(), 300);
  }
  
  // Remember dismissal for 3 days
  localStorage.setItem('ios-prompt-dismissed', 'true');
  localStorage.setItem('ios-prompt-dismissed-time', Date.now().toString());
}

// Show iOS prompt after a delay (only on iOS)
setTimeout(showiOSInstallPrompt, 8000);

// Periodic reminder for install (every page view after 3 visits)
function checkInstallReminder() {
  if (isAppInstalled()) return;
  
  let visitCount = parseInt(localStorage.getItem('pwa-visit-count') || '0');
  visitCount++;
  localStorage.setItem('pwa-visit-count', visitCount.toString());
  
  // Show reminder after 3 visits
  if (visitCount >= 3 && visitCount % 3 === 0 && deferredPrompt) {
    setTimeout(() => {
      showInstallButton();
    }, 10000); // Show after 10 seconds on page
  }
}

// Check on page load
checkInstallReminder();