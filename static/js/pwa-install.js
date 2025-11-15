// Enhanced PWA Installation with Progress Animation
// Save as: static/js/pwa-install.js

let deferredPrompt;
let installNotification;
let progressModal;

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
  }

  // Create UI elements
  createInstallNotification();
  createProgressModal();

  // Listen for beforeinstallprompt
  window.addEventListener('beforeinstallprompt', (e) => {
    console.log('[PWA] beforeinstallprompt event fired');
    e.preventDefault();
    deferredPrompt = e;
    showInstallNotification();
  });

  // Listen for app installed
  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App installed successfully');
    hideInstallNotification();
    showInstallationSuccess();
  });

  // Check if already installed
  if (isAppInstalled()) {
    console.log('[PWA] App is already installed');
    hideInstallNotification();
  }
}

async function registerServiceWorker() {
  try {
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
        
        console.log('[PWA] Service Worker registered:', registration.scope);
        registered = true;
        
        // Listen for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installing') {
              console.log('[PWA] Service Worker installing...');
            }
            if (newWorker.state === 'installed') {
              console.log('[PWA] Service Worker installed');
              if (navigator.serviceWorker.controller) {
                showUpdateMessage();
              }
            }
            if (newWorker.state === 'activated') {
              console.log('[PWA] Service Worker activated');
            }
          });
        });
        
        break;
      } catch (err) {
        console.log(`[PWA] Failed from ${path}, trying next...`);
      }
    }
    
    if (!registered) {
      console.error('[PWA] Could not register service worker');
    }
    
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

function createInstallNotification() {
  const existing = document.getElementById('pwa-install-notification');
  if (existing) existing.remove();

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
        <p class="mb-0">Quick access & offline mode</p>
      </div>
      <div class="pwa-notification-actions">
        <button class="btn btn-light btn-sm" onclick="startInstallation()">
          <i class="fas fa-download me-1"></i>Install Now
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

function createProgressModal() {
  const existing = document.getElementById('pwa-progress-modal');
  if (existing) existing.remove();

  progressModal = document.createElement('div');
  progressModal.id = 'pwa-progress-modal';
  progressModal.className = 'pwa-progress-modal';
  progressModal.innerHTML = `
    <div class="pwa-progress-overlay"></div>
    <div class="pwa-progress-container">
      <div class="pwa-progress-content">
        <!-- Header -->
        <div class="pwa-progress-header">
          <img src="https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg" 
               alt="FUTO BME" class="pwa-progress-logo">
          <h4 class="mb-1">Installing FUTO BME App</h4>
          <p class="text-muted mb-0" id="progress-status">Preparing installation...</p>
        </div>

        <!-- Progress Animation -->
        <div class="pwa-progress-animation">
          <!-- Downloading Icon -->
          <div class="download-animation" id="download-animation">
            <div class="phone-outline">
              <i class="fas fa-mobile-alt"></i>
            </div>
            <div class="download-arrow">
              <i class="fas fa-arrow-down"></i>
            </div>
          </div>

          <!-- Installing Icon -->
          <div class="installing-animation" id="installing-animation" style="display: none;">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Installing...</span>
            </div>
            <div class="installing-dots">
              <span></span><span></span><span></span>
            </div>
          </div>

          <!-- Success Icon -->
          <div class="success-animation" id="success-animation" style="display: none;">
            <div class="success-checkmark">
              <div class="check-icon">
                <span class="icon-line line-tip"></span>
                <span class="icon-line line-long"></span>
                <div class="icon-circle"></div>
                <div class="icon-fix"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="pwa-progress-bar-container">
          <div class="pwa-progress-bar">
            <div class="pwa-progress-fill" id="progress-fill"></div>
          </div>
          <div class="pwa-progress-text">
            <span id="progress-percentage">0%</span>
            <span id="progress-size">0 KB / 0 KB</span>
          </div>
        </div>

        <!-- Details -->
        <div class="pwa-progress-details">
          <div class="detail-item">
            <i class="fas fa-check-circle text-success"></i>
            <span id="detail-1">Checking requirements...</span>
          </div>
          <div class="detail-item" id="detail-2-container" style="opacity: 0.3;">
            <i class="fas fa-circle text-muted"></i>
            <span id="detail-2">Downloading resources...</span>
          </div>
          <div class="detail-item" id="detail-3-container" style="opacity: 0.3;">
            <i class="fas fa-circle text-muted"></i>
            <span id="detail-3">Installing application...</span>
          </div>
          <div class="detail-item" id="detail-4-container" style="opacity: 0.3;">
            <i class="fas fa-circle text-muted"></i>
            <span id="detail-4">Finalizing setup...</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="pwa-progress-actions">
          <button class="btn btn-link text-danger" onclick="cancelInstallation()" id="cancel-btn">
            Cancel
          </button>
          <button class="btn btn-primary" onclick="closeProgressModal()" id="done-btn" style="display: none;">
            <i class="fas fa-check me-1"></i>Done
          </button>
          <button class="btn btn-success" onclick="openInstalledApp()" id="open-btn" style="display: none;">
            <i class="fas fa-external-link-alt me-1"></i>Open App
          </button>
        </div>
      </div>
    </div>
  `;
  
  progressModal.style.display = 'none';
  document.body.appendChild(progressModal);
}

function showInstallNotification() {
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
    }, 500);
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
  localStorage.setItem('pwa-install-dismissed', 'true');
  localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
  console.log('[PWA] Install notification dismissed by user');
}

// Main installation flow
async function startInstallation() {
  console.log('[PWA] Starting installation...');
  
  if (!deferredPrompt) {
    console.log('[PWA] No deferred prompt available');
    showInstallInstructions();
    return;
  }

  // Hide notification
  hideInstallNotification();
  
  // Show progress modal
  showProgressModal();
  
  // Simulate download progress
  await simulateDownloadProgress();
  
  // Trigger actual install
  await triggerBrowserInstall();
}

function showProgressModal() {
  progressModal.style.display = 'flex';
  setTimeout(() => {
    progressModal.classList.add('show');
  }, 100);
  
  // Reset UI
  document.getElementById('progress-fill').style.width = '0%';
  document.getElementById('progress-percentage').textContent = '0%';
  document.getElementById('cancel-btn').style.display = 'inline-block';
  document.getElementById('done-btn').style.display = 'none';
  document.getElementById('open-btn').style.display = 'none';
  
  // Reset animations
  document.getElementById('download-animation').style.display = 'block';
  document.getElementById('installing-animation').style.display = 'none';
  document.getElementById('success-animation').style.display = 'none';
}

async function simulateDownloadProgress() {
  const totalSize = 2500; // KB (simulated)
  const steps = [
    { progress: 15, time: 300, status: 'Checking requirements...', detail: 1 },
    { progress: 35, time: 600, status: 'Downloading resources...', detail: 2 },
    { progress: 65, time: 800, status: 'Caching files...', detail: 2 },
    { progress: 85, time: 500, status: 'Installing application...', detail: 3 },
    { progress: 95, time: 400, status: 'Finalizing setup...', detail: 4 }
  ];
  
  for (const step of steps) {
    await new Promise(resolve => setTimeout(resolve, step.time));
    
    // Update progress bar
    updateProgress(step.progress, totalSize);
    
    // Update status
    document.getElementById('progress-status').textContent = step.status;
    
    // Update detail icons
    updateDetailIcon(step.detail);
    
    // Switch animation at 65%
    if (step.progress === 65) {
      document.getElementById('download-animation').style.display = 'none';
      document.getElementById('installing-animation').style.display = 'flex';
    }
  }
}

function updateProgress(percentage, totalSize) {
  const currentSize = Math.floor((percentage / 100) * totalSize);
  
  document.getElementById('progress-fill').style.width = `${percentage}%`;
  document.getElementById('progress-percentage').textContent = `${percentage}%`;
  document.getElementById('progress-size').textContent = `${currentSize} KB / ${totalSize} KB`;
}

function updateDetailIcon(detailNumber) {
  // Update previous details to complete
  for (let i = 1; i <= detailNumber; i++) {
    const container = document.getElementById(`detail-${i}-container`);
    const icon = container.querySelector('i');
    
    container.style.opacity = '1';
    icon.className = 'fas fa-check-circle text-success';
  }
  
  // Highlight current detail
  if (detailNumber < 4) {
    const nextContainer = document.getElementById(`detail-${detailNumber + 1}-container`);
    nextContainer.style.opacity = '1';
    const nextIcon = nextContainer.querySelector('i');
    nextIcon.className = 'fas fa-spinner fa-spin text-primary';
  }
}

async function triggerBrowserInstall() {
  try {
    console.log('[PWA] Triggering browser install prompt...');
    
    // Show browser prompt
    await deferredPrompt.prompt();
    
    // Wait for user choice
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`[PWA] User response: ${outcome}`);
    
    if (outcome === 'accepted') {
      console.log('[PWA] User accepted installation');
      
      // Complete progress
      updateProgress(100, 2500);
      document.getElementById('progress-status').textContent = 'Installation complete!';
      updateDetailIcon(4);
      
      // Show success animation
      document.getElementById('installing-animation').style.display = 'none';
      document.getElementById('success-animation').style.display = 'flex';
      
      // Trigger success animation
      setTimeout(() => {
        document.querySelector('.success-checkmark').classList.add('animate');
      }, 100);
      
      // Update buttons
      setTimeout(() => {
        document.getElementById('cancel-btn').style.display = 'none';
        document.getElementById('done-btn').style.display = 'inline-block';
        document.getElementById('open-btn').style.display = 'inline-block';
        
        // Play success sound (optional)
        playSuccessSound();
        
        // Show confetti (optional)
        showConfetti();
      }, 1000);
      
    } else {
      console.log('[PWA] User dismissed installation');
      closeProgressModal();
      
      // Show notification again after 1 minute
      setTimeout(() => {
        if (!isAppInstalled()) {
          showInstallNotification();
        }
      }, 60000);
    }
    
  } catch (error) {
    console.error('[PWA] Installation error:', error);
    showInstallError();
  }
  
  deferredPrompt = null;
}

function cancelInstallation() {
  console.log('[PWA] Installation cancelled by user');
  closeProgressModal();
  
  // Show notification again
  setTimeout(() => {
    if (!isAppInstalled()) {
      showInstallNotification();
    }
  }, 2000);
}

function closeProgressModal() {
  progressModal.classList.remove('show');
  setTimeout(() => {
    progressModal.style.display = 'none';
  }, 300);
}

function openInstalledApp() {
  // Try to open the app in standalone mode
  if (window.matchMedia('(display-mode: standalone)').matches) {
    closeProgressModal();
  } else {
    // If not in standalone, just close modal
    closeProgressModal();
    showToast('success', 'App Installed!', 'Find the FUTO BME app on your home screen');
  }
}

function showInstallationSuccess() {
  if (progressModal.style.display !== 'flex') {
    showToast('success', 'Installation Complete!', 'FUTO BME app is now installed on your device');
  }
}

function showInstallError() {
  closeProgressModal();
  showToast('error', 'Installation Failed', 'Please try again or install manually from browser menu');
}

function showInstallInstructions() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  
  let instructions = '';
  if (isIOS) {
    instructions = 'Tap the Share button <i class="fas fa-share"></i> then "Add to Home Screen"';
  } else {
    instructions = 'Look for the install option in your browser menu or address bar';
  }
  
  showToast('info', 'Install Instructions', instructions);
}

// Utility functions
function isAppInstalled() {
  return window.matchMedia('(display-mode: standalone)').matches || 
         window.navigator.standalone === true;
}

function showToast(type, title, message) {
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
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 500);
  }, 5000);
}

function playSuccessSound() {
  // Optional: Play a success sound
  try {
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE=');
    audio.volume = 0.3;
    audio.play().catch(() => {});
  } catch (e) {
    // Silently fail if audio doesn't work
  }
}

function showConfetti() {
  // Simple confetti effect
  const colors = ['#8B1538', '#D4AF37', '#6B3FA0'];
  const confettiCount = 30;
  
  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confetti.style.left = Math.random() * 100 + '%';
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.animationDelay = Math.random() * 0.5 + 's';
    confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
    
    progressModal.appendChild(confetti);
    
    setTimeout(() => confetti.remove(), 4000);
  }
}

function showUpdateMessage() {
  showToast('info', 'Update Available', 
    '<button class="btn btn-sm btn-light mt-2" onclick="updateServiceWorker()">Update Now</button>'
  );
}

function updateServiceWorker() {
  navigator.serviceWorker.getRegistration().then((registration) => {
    if (registration && registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  });
}

// Network status
window.addEventListener('online', () => {
  showToast('success', 'Back Online!', 'Internet connection restored');
});

window.addEventListener('offline', () => {
  showToast('warning', 'Offline Mode', 'Working offline - Some features may be limited');
});

// Visit tracking
function checkInstallReminder() {
  if (isAppInstalled()) return;
  
  let visitCount = parseInt(localStorage.getItem('pwa-visit-count') || '0');
  visitCount++;
  localStorage.setItem('pwa-visit-count', visitCount.toString());
  
  if (visitCount >= 3 && visitCount % 3 === 0 && deferredPrompt) {
    setTimeout(() => {
      showInstallNotification();
    }, 5000);
  }
}

checkInstallReminder();

// Global functions
window.startInstallation = startInstallation;
window.dismissInstallNotification = dismissInstallNotification;
window.cancelInstallation = cancelInstallation;
window.closeProgressModal = closeProgressModal;
window.openInstalledApp = openInstalledApp;
window.updateServiceWorker = updateServiceWorker;

console.log('[PWA] Script loaded successfully');