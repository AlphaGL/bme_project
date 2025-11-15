// Enhanced PWA Installation Handler with Notification Style
// Save as: static/js/pwa-install.js

let deferredPrompt;
let installNotification;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePWA);
} else {
  initializePWA();
}

function initializePWA() {
  console.log('[PWA] Initializing...');
  
  // Register service worker
  if ('serviceWorker' in navigator) {
    registerServiceWorker();
  } else {
    console.log('[PWA] Service Workers not supported');
  }

  // Create install notification
  createInstallNotification();

  // Listen for beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] beforeinstallprompt event fired');
    e.preventDefault();
    deferredPrompt = e;
    showInstallNotification();
  });

  // Listen for app installed event
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    hideInstallNotification();
    showSuccessMessage();
  });

  // Check if already installed
  if (isAppInstalled()) {
    console.log('[PWA] App is already installed');
    hideInstallNotification();
  }
}

async function registerServiceWorker() {
  try {
    // Try multiple possible paths for service worker
    const possiblePaths = [
      '/service-worker.js',
      '/static/js/service-worker.js',
      '/sw.js'
    ];
    
    let registered = false;
    
    for (const path of possiblePaths) {
      try {
        const registration = await navigator.serviceWorker.register(path, {
          scope: '/'
        });
        
        console.log('[PWA] Service Worker registered successfully:', registration.scope);
        console.log('[PWA] Service Worker path:', path);
        registered = true;
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              showUpdateMessage();
            }
          });
        });
        
        break; // Exit loop if successful
      } catch (err) {
        console.log(`[PWA] Failed to register from ${path}, trying next...`);
      }
    }
    
    if (!registered) {
      console.error('[PWA] Could not register service worker from any path');
    }
    
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

function createInstallNotification() {
  // Remove any existing notification
  const existing = document.getElementById('pwa-install-notification');
  if (existing) {
    existing.remove();
  }

  // Create notification element
  installNotification = document.createElement('div');
  installNotification.id = 'pwa-install-notification';
  installNotification.className = 'pwa-install-notification';
  installNotification.innerHTML = `
    <div class="pwa-notification-content">
      <div class="pwa-notification-icon">
        <i class="fas fa-mobile-alt"></i>
      </div>
      <div class="pwa-notification-text">
        <h6 class="mb-1">Install FUTO BME App</h6>
        <p class="mb-0">Get quick access & work offline</p>
      </div>
      <div class="pwa-notification-actions">
        <button class="btn btn-light btn-sm" onclick="handleInstallClick()">
          <i class="fas fa-download me-1"></i>Install
        </button>
        <button class="btn btn-link btn-sm text-white" onclick="dismissInstallNotification()">
          Later
        </button>
      </div>
    </div>
  `;
  
  installNotification.style.display = 'none';
  document.body.appendChild(installNotification);
}

function showInstallNotification() {
  // Check if user dismissed recently
  const dismissed = localStorage.getItem('pwa-install-dismissed');
  const dismissedTime = localStorage.getItem('pwa-install-dismissed-time');
  
  if (dismissed === 'true' && dismissedTime) {
    const hoursSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60);
    if (hoursSinceDismissed < 24) {
      console.log('[PWA] Install notification dismissed recently');
      return;
    }
  }
  
  if (installNotification && deferredPrompt) {
    console.log('[PWA] Showing install notification');
    installNotification.style.display = 'block';
    setTimeout(() => {
      installNotification.classList.add('show');
    }, 500); // Show after 0.5 seconds
  }
}

function hideInstallNotification() {
  if (installNotification) {
    installNotification.classList.remove('show');
    setTimeout(() => {
      installNotification.style.display = 'none';
    }, 300);
  }
}

function dismissInstallNotification() {
  hideInstallNotification();
  // Remember dismissal for 24 hours
  localStorage.setItem('pwa-install-dismissed', 'true');
  localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
  console.log('[PWA] Install notification dismissed by user');
}

async function handleInstallClick() {
  console.log('[PWA] Install button clicked');
  
  if (!deferredPrompt) {
    console.log('[PWA] No deferred prompt available');
    showInstallInstructions();
    return;
  }

  // Hide notification
  hideInstallNotification();

  try {
    // Show install prompt
    await deferredPrompt.prompt();

    // Wait for user choice
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`[PWA] User response: ${outcome}`);

    if (outcome === 'accepted') {
      console.log('[PWA] User accepted the install prompt');
      showSuccessMessage();
    } else {
      console.log('[PWA] User dismissed the install prompt');
      // Show notification again after 1 minute
      setTimeout(() => {
        if (!isAppInstalled()) {
          showInstallNotification();
        }
      }, 60000);
    }
  } catch (error) {
    console.error('[PWA] Install prompt error:', error);
  }

  // Clear the deferred prompt
  deferredPrompt = null;
}

function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.navigator.standalone === true;
}

function showInstallInstructions() {
  const toast = createToast(
    'info',
    'Install Instructions',
    detectBrowserInstructions(),
    8000
  );
  document.body.appendChild(toast);
}

function detectBrowserInstructions() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  const isChrome = /Chrome/.test(navigator.userAgent);
  const isFirefox = /Firefox/.test(navigator.userAgent);
  const isSafari = /Safari/.test(navigator.userAgent) && !isChrome;
  
  if (isIOS) {
    return 'Tap the Share button <i class="fas fa-share"></i> then select "Add to Home Screen"';
  } else if (isChrome) {
    return 'Look for the install icon <i class="fas fa-plus-circle"></i> in your browser\'s address bar';
  } else if (isFirefox) {
    return 'Tap the menu <i class="fas fa-ellipsis-v"></i> and select "Install"';
  } else if (isSafari) {
    return 'This feature requires Chrome, Firefox, or Safari on iOS';
  } else {
    return 'Look for the install option in your browser\'s menu';
  }
}

function showSuccessMessage() {
  const toast = createToast(
    'success',
    'Success!',
    'FUTO BME Portal installed successfully',
    5000
  );
  document.body.appendChild(toast);
}

function showUpdateMessage() {
  const toast = createToast(
    'info',
    'Update Available',
    '<button class="btn btn-sm btn-light mt-2" onclick="updateServiceWorker()">Update Now</button>',
    0 // Don't auto-dismiss
  );
  document.body.appendChild(toast);
}

function createToast(type, title, message, duration = 5000) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} pwa-toast`;
  
  const icons = {
    success: 'fa-check-circle',
    error: 'fa-times-circle',
    warning: 'fa-exclamation-triangle',
    info: 'fa-info-circle'
  };
  
  toast.innerHTML = `
    <div class="d-flex align-items-start">
      <i class="fas ${icons[type]} me-2 mt-1"></i>
      <div class="flex-grow-1">
        <strong>${title}</strong><br>
        ${message}
      </div>
      <button type="button" class="btn-close ms-2" onclick="this.parentElement.parentElement.remove()"></button>
    </div>
  `;
  
  if (duration > 0) {
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 500);
    }, duration);
  }
  
  return toast;
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
  console.log('[PWA] Connection restored');
  const toast = createToast('success', 'Back Online!', 'Internet connection restored', 3000);
  document.body.appendChild(toast);
});

window.addEventListener('offline', () => {
  console.log('[PWA] Connection lost');
  const toast = createToast('warning', 'Offline Mode', 'Working offline - Some features may be limited', 3000);
  document.body.appendChild(toast);
});

// Periodic reminder (show after 3 visits)
function checkInstallReminder() {
  if (isAppInstalled()) return;
  
  let visitCount = parseInt(localStorage.getItem('pwa-visit-count') || '0');
  visitCount++;
  localStorage.setItem('pwa-visit-count', visitCount.toString());
  
  console.log(`[PWA] Visit count: ${visitCount}`);
  
  if (visitCount >= 3 && visitCount % 3 === 0 && deferredPrompt) {
    setTimeout(() => {
      showInstallNotification();
    }, 5000);
  }
}

// Check on page load
checkInstallReminder();

// Make functions globally available
window.handleInstallClick = handleInstallClick;
window.dismissInstallNotification = dismissInstallNotification;
window.updateServiceWorker = updateServiceWorker;

console.log('[PWA] Script loaded successfully');