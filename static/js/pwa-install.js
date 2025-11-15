// Enhanced PWA Installation Handler - FIXED VERSION
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
  window.addEventListener('appinstalled', (e) => {
    console.log('[PWA] App installed successfully');
    hideInstallNotification();
    showSuccessMessage();
    deferredPrompt = null;
  });

  // Check if already installed
  if (isAppInstalled()) {
    console.log('[PWA] App is already installed');
    hideInstallNotification();
  }
}

async function registerServiceWorker() {
  try {
    // Try to register service worker
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/'
    });
    
    console.log('[PWA] Service Worker registered successfully:', registration.scope);
    
    // Listen for messages from service worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      handleServiceWorkerMessage(event.data);
    });
    
    // Check for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      console.log('[PWA] New service worker found, installing...');
      
      newWorker.addEventListener('statechange', () => {
        console.log('[PWA] Service worker state:', newWorker.state);
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          showUpdateMessage();
        }
      });
    });
    
    // Check for updates on page load
    registration.update();
    
  } catch (error) {
    console.error('[PWA] Service Worker registration failed:', error);
  }
}

function handleServiceWorkerMessage(data) {
  console.log('[PWA] Message from service worker:', data);
  
  if (data.type === 'INSTALL_PROGRESS') {
    updateInstallProgress(data);
  } else if (data.type === 'INSTALL_COMPLETE') {
    console.log('[PWA] Service worker installation complete');
  } else if (data.type === 'INSTALL_ERROR') {
    console.error('[PWA] Service worker installation error:', data.error);
  }
}

function updateInstallProgress(data) {
  const progressDialog = document.querySelector('.pwa-download-progress');
  if (!progressDialog) return;
  
  const statusSpan = progressDialog.querySelector('#download-status');
  if (statusSpan && data.percentage) {
    if (data.percentage < 30) {
      statusSpan.textContent = `Downloading core files... (${data.current}/${data.total})`;
    } else if (data.percentage < 60) {
      statusSpan.textContent = `Downloading styles... (${data.current}/${data.total})`;
    } else if (data.percentage < 90) {
      statusSpan.textContent = `Downloading assets... (${data.current}/${data.total})`;
    } else {
      statusSpan.textContent = `Finalizing... (${data.current}/${data.total})`;
    }
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
        <button class="btn btn-light btn-sm" id="pwa-install-btn">
          <i class="fas fa-download me-1"></i>Install
        </button>
        <button class="btn btn-link btn-sm text-white" id="pwa-dismiss-btn">
          Later
        </button>
      </div>
    </div>
  `;
  
  installNotification.style.display = 'none';
  document.body.appendChild(installNotification);
  
  // Add event listeners
  document.getElementById('pwa-install-btn').addEventListener('click', handleInstallClick);
  document.getElementById('pwa-dismiss-btn').addEventListener('click', dismissInstallNotification);
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

  // Show installing feedback
  const installBtn = document.getElementById('pwa-install-btn');
  const originalHTML = installBtn.innerHTML;
  installBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Installing...';
  installBtn.disabled = true;

  // Calculate app size and show progress
  const appSize = await estimateAppSize();
  const progressDialog = showInstallProgress(appSize);

  try {
    // Show install prompt
    console.log('[PWA] Showing install prompt...');
    await deferredPrompt.prompt();

    // Wait for user choice
    const choiceResult = await deferredPrompt.userChoice;
    console.log(`[PWA] User response: ${choiceResult.outcome}`);

    if (choiceResult.outcome === 'accepted') {
      console.log('[PWA] User accepted the install prompt');
      
      // Start progress tracking
      trackInstallProgress(progressDialog, appSize);
      
      // Hide install notification after a delay
      setTimeout(() => {
        hideInstallNotification();
      }, 1000);
      
      // Clear dismissal flags
      localStorage.removeItem('pwa-install-dismissed');
      localStorage.removeItem('pwa-install-dismissed-time');
    } else {
      console.log('[PWA] User dismissed the install prompt');
      
      // Remove progress dialog
      progressDialog.remove();
      
      // Restore button
      installBtn.innerHTML = originalHTML;
      installBtn.disabled = false;
      
      // Show notification again after 1 minute
      setTimeout(() => {
        if (!isAppInstalled() && deferredPrompt) {
          showInstallNotification();
        }
      }, 60000);
    }
  } catch (error) {
    console.error('[PWA] Install prompt error:', error);
    
    // Remove progress dialog
    progressDialog.remove();
    
    // Restore button
    installBtn.innerHTML = originalHTML;
    installBtn.disabled = false;
    
    showErrorMessage('Installation failed. Please try again.');
  }

  // Clear the deferred prompt
  deferredPrompt = null;
}

async function estimateAppSize() {
  // Resources to download
  const resources = [
    '/',
    '/offline/',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg'
  ];

  let totalSize = 0;
  const sizes = [];

  try {
    // Try to get actual sizes using HEAD requests
    const sizePromises = resources.map(async (url) => {
      try {
        const response = await fetch(url, { method: 'HEAD' });
        const size = parseInt(response.headers.get('content-length') || '0');
        return size;
      } catch {
        // Estimate if HEAD request fails
        return estimateResourceSize(url);
      }
    });

    sizes.push(...await Promise.all(sizePromises));
    totalSize = sizes.reduce((sum, size) => sum + size, 0);
  } catch (error) {
    console.log('[PWA] Could not determine exact size, using estimate');
  }

  // If we couldn't get sizes, use estimates
  if (totalSize === 0) {
    totalSize = 2.5 * 1024 * 1024; // Estimate ~2.5 MB
  }

  return totalSize;
}

function estimateResourceSize(url) {
  // Rough estimates based on resource type
  if (url.includes('bootstrap.min.css')) return 200 * 1024; // ~200KB
  if (url.includes('bootstrap.bundle.min.js')) return 80 * 1024; // ~80KB
  if (url.includes('font-awesome')) return 300 * 1024; // ~300KB
  if (url.includes('.jpg') || url.includes('.png')) return 100 * 1024; // ~100KB
  return 50 * 1024; // Default 50KB
}

function showInstallProgress(totalSize) {
  const progressDialog = document.createElement('div');
  progressDialog.className = 'pwa-download-progress show';
  progressDialog.innerHTML = `
    <div class="pwa-download-percentage" id="download-percentage">0%</div>
    <div class="pwa-download-progress-header">
      <div class="pwa-download-progress-icon">
        <i class="fas fa-download"></i>
      </div>
      <div class="pwa-download-progress-text">
        <h6>Installing FUTO BME</h6>
        <p>
          <span id="download-current">0 MB</span> / 
          <span id="download-total">${formatBytes(totalSize)}</span>
        </p>
      </div>
    </div>
    <div class="pwa-download-progress-bar-container">
      <div class="pwa-download-progress-bar-fill" id="download-progress-bar"></div>
    </div>
    <div class="pwa-download-status">
      <span id="download-status">Preparing installation...</span>
    </div>
    <div class="pwa-download-speed" id="download-speed" style="display: none;">
      <i class="fas fa-tachometer-alt"></i>
      <span id="speed-value">0 KB/s</span>
    </div>
  `;
  
  document.body.appendChild(progressDialog);
  return progressDialog;
}

function trackInstallProgress(progressDialog, totalSize) {
  const progressBar = progressDialog.querySelector('#download-progress-bar');
  const currentSpan = progressDialog.querySelector('#download-current');
  const statusSpan = progressDialog.querySelector('#download-status');
  const percentageSpan = progressDialog.querySelector('#download-percentage');
  const speedContainer = progressDialog.querySelector('#download-speed');
  const speedValue = progressDialog.querySelector('#speed-value');
  
  let downloadedSize = 0;
  let lastSize = 0;
  let startTime = Date.now();
  const updateInterval = 100; // Update every 100ms
  const estimatedDuration = 3000; // Estimate 3 seconds for installation
  const sizePerUpdate = totalSize / (estimatedDuration / updateInterval);
  
  statusSpan.textContent = 'Downloading resources...';
  speedContainer.style.display = 'flex';
  
  const progressInterval = setInterval(() => {
    downloadedSize += sizePerUpdate;
    
    // Calculate download speed
    const elapsed = Date.now() - startTime;
    const bytesDownloaded = downloadedSize - lastSize;
    const speed = (bytesDownloaded / (updateInterval / 1000)); // bytes per second
    lastSize = downloadedSize;
    
    if (speed > 0) {
      speedValue.textContent = formatSpeed(speed);
    }
    
    if (downloadedSize >= totalSize) {
      downloadedSize = totalSize;
      clearInterval(progressInterval);
      
      // Show completion
      progressDialog.classList.add('complete');
      progressBar.style.width = '100%';
      currentSpan.textContent = formatBytes(totalSize);
      percentageSpan.textContent = '100%';
      statusSpan.textContent = 'Installation complete!';
      speedContainer.style.display = 'none';
      
      // Change icon to checkmark
      const icon = progressDialog.querySelector('.pwa-download-progress-icon i');
      icon.className = 'fas fa-check-circle';
      
      // Hide after 2 seconds and show success
      setTimeout(() => {
        progressDialog.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
          progressDialog.remove();
          showSuccessMessage();
        }, 300);
      }, 2000);
    } else {
      const percentage = Math.round((downloadedSize / totalSize) * 100);
      progressBar.style.width = `${percentage}%`;
      currentSpan.textContent = formatBytes(downloadedSize);
      percentageSpan.textContent = `${percentage}%`;
      
      // Update status based on progress
      if (percentage < 30) {
        statusSpan.textContent = 'Downloading core files...';
      } else if (percentage < 60) {
        statusSpan.textContent = 'Downloading styles and scripts...';
      } else if (percentage < 90) {
        statusSpan.textContent = 'Downloading assets...';
      } else {
        statusSpan.textContent = 'Finalizing installation...';
      }
    }
  }, updateInterval);
  
  // Listen for actual app install completion
  window.addEventListener('appinstalled', () => {
    clearInterval(progressInterval);
    downloadedSize = totalSize;
    
    progressDialog.classList.add('complete');
    progressBar.style.width = '100%';
    currentSpan.textContent = formatBytes(totalSize);
    percentageSpan.textContent = '100%';
    statusSpan.textContent = 'Installation complete!';
    speedContainer.style.display = 'none';
    
    // Change icon to checkmark
    const icon = progressDialog.querySelector('.pwa-download-progress-icon i');
    icon.className = 'fas fa-check-circle';
    
    setTimeout(() => {
      progressDialog.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        progressDialog.remove();
        showSuccessMessage();
      }, 300);
    }, 1500);
  }, { once: true });
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 MB';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatSpeed(bytesPerSecond) {
  const k = 1024;
  
  if (bytesPerSecond < k) {
    return `${Math.round(bytesPerSecond)} B/s`;
  } else if (bytesPerSecond < k * k) {
    return `${Math.round(bytesPerSecond / k)} KB/s`;
  } else {
    return `${(bytesPerSecond / (k * k)).toFixed(1)} MB/s`;
  }
}

function isAppInstalled() {
  // Check if running in standalone mode
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return true;
  }
  
  // Check for iOS standalone mode
  if (window.navigator.standalone === true) {
    return true;
  }
  
  return false;
}

function showInstallInstructions() {
  const toast = createToast(
    'info',
    'Install Instructions',
    detectBrowserInstructions(),
    10000
  );
  document.body.appendChild(toast);
}

function detectBrowserInstructions() {
  const userAgent = navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  const isChrome = /chrome/.test(userAgent) && !/edg/.test(userAgent);
  const isFirefox = /firefox/.test(userAgent);
  const isSafari = /safari/.test(userAgent) && !isChrome;
  const isEdge = /edg/.test(userAgent);
  
  if (isIOS) {
    if (isSafari) {
      return 'Tap the Share button <i class="fas fa-share"></i> at the bottom, then scroll and select "Add to Home Screen"';
    }
    return 'Please use Safari browser to install this app on iOS';
  } else if (isChrome) {
    return 'Look for the install icon <i class="fas fa-download"></i> in your browser\'s address bar, or check the menu <i class="fas fa-ellipsis-v"></i> for "Install app"';
  } else if (isEdge) {
    return 'Look for the install icon <i class="fas fa-download"></i> in the address bar, or click the menu <i class="fas fa-ellipsis-h"></i> and select "Apps" → "Install this site as an app"';
  } else if (isFirefox) {
    return 'Tap the menu <i class="fas fa-ellipsis-v"></i> and select "Install" or "Add to Home screen"';
  } else {
    return 'Look for the install option in your browser\'s menu. PWA installation is supported in Chrome, Edge, and Firefox.';
  }
}

function showSuccessMessage() {
  const toast = createToast(
    'success',
    '🎉 Success!',
    'FUTO BME Portal installed successfully! You can now access it from your home screen.',
    6000
  );
  document.body.appendChild(toast);
}

function showErrorMessage(message) {
  const toast = createToast(
    'error',
    'Installation Failed',
    message,
    5000
  );
  document.body.appendChild(toast);
}

function showUpdateMessage() {
  const toast = createToast(
    'info',
    'Update Available',
    'A new version is available. <button class="btn btn-sm btn-light mt-2" onclick="updateServiceWorker()">Update Now</button>',
    0 // Don't auto-dismiss
  );
  document.body.appendChild(toast);
}

function createToast(type, title, message, duration = 5000) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} pwa-toast`;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 350px;
    min-width: 300px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    animation: slideIn 0.3s ease;
  `;
  
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
      <button type="button" class="btn-close ms-2" aria-label="Close"></button>
    </div>
  `;
  
  // Add close functionality
  toast.querySelector('.btn-close').addEventListener('click', () => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  });
  
  if (duration > 0) {
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
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
  const toast = createToast('success', '✓ Back Online!', 'Internet connection restored', 3000);
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
window.updateServiceWorker = updateServiceWorker;

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

console.log('[PWA] Script loaded successfully');