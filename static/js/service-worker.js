// Service Worker for FUTO BME PWA - FIXED VERSION
// Place at: static/js/service-worker.js or root/service-worker.js

const CACHE_NAME = 'futo-bme-v1.2.0';
const OFFLINE_URL = '/offline/';

// Essential files to cache immediately
const STATIC_CACHE = [
  '/',
  '/offline/',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg'
];

// Install event - Cache essential resources with progress tracking
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching essential assets');
        
        let cachedCount = 0;
        const totalCount = STATIC_CACHE.length;
        
        // Notify clients of progress
        const notifyProgress = (current, total) => {
          self.clients.matchAll().then(clients => {
            clients.forEach(client => {
              client.postMessage({
                type: 'INSTALL_PROGRESS',
                current: current,
                total: total,
                percentage: Math.round((current / total) * 100)
              });
            });
          });
        };
        
        // Cache files individually with progress tracking
        return Promise.allSettled(
          STATIC_CACHE.map(async (url, index) => {
            try {
              const response = await fetch(url);
              if (response.ok) {
                await cache.put(url, response);
                cachedCount++;
                notifyProgress(cachedCount, totalCount);
                console.log(`[Service Worker] Cached ${cachedCount}/${totalCount}: ${url}`);
              }
              return response;
            } catch (err) {
              console.warn(`[Service Worker] Failed to cache ${url}:`, err.message);
              cachedCount++;
              notifyProgress(cachedCount, totalCount);
              return null;
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        
        // Notify completion
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'INSTALL_COMPLETE'
            });
          });
        });
        
        // Force the waiting service worker to become the active service worker
        return self.skipWaiting();
      })
      .catch(err => {
        console.error('[Service Worker] Installation failed:', err);
        
        // Notify error
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'INSTALL_ERROR',
              error: err.message
            });
          });
        });
      })
  );
});

// Activate event - Clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Activation complete');
        // Take control of all pages immediately
        return self.clients.claim();
      })
      .catch(err => {
        console.error('[Service Worker] Activation error:', err);
      })
  );
});

// Fetch event - Network first, then cache, then offline
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip chrome extensions and other protocols
  if (!event.request.url.startsWith('http')) {
    return;
  }

  // Skip API calls and admin endpoints (they need fresh data)
  const url = new URL(event.request.url);
  if (url.pathname.includes('/admin/') || 
      url.pathname.includes('/api/') ||
      url.pathname.includes('/student/payment/') ||
      url.pathname.includes('/verify-payment/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Check if valid response
        if (!response || response.status !== 200 || response.type === 'error') {
          return response;
        }

        // Clone the response
        const responseToCache = response.clone();

        // Cache the fetched resource (async, don't wait)
        caches.open(CACHE_NAME).then((cache) => {
          // Only cache same-origin or allowed CDN resources
          if (url.origin === location.origin || isAllowedCDN(url.href)) {
            cache.put(event.request, responseToCache).catch(err => {
              console.warn('[Service Worker] Failed to cache:', url.href);
            });
          }
        });

        return response;
      })
      .catch((error) => {
        console.log('[Service Worker] Fetch failed, trying cache:', event.request.url);
        
        // Network failed, try cache
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            console.log('[Service Worker] Serving from cache:', event.request.url);
            return cachedResponse;
          }

          // If navigation request and not in cache, show offline page
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL).then((offlinePage) => {
              return offlinePage || new Response(
                '<!DOCTYPE html><html><head><title>Offline</title></head><body><h1>You are offline</h1><p>Please check your internet connection.</p></body></html>',
                {
                  status: 503,
                  statusText: 'Service Unavailable',
                  headers: new Headers({
                    'Content-Type': 'text/html'
                  })
                }
              );
            });
          }

          // For other requests, return a generic offline response
          return new Response('Offline', {
            status: 503,
            statusText: 'Service Unavailable'
          });
        });
      })
  );
});

// Helper function to identify allowed CDN resources
function isAllowedCDN(url) {
  const allowedDomains = [
    'cdn.jsdelivr.net',
    'cdnjs.cloudflare.com',
    'res.cloudinary.com',
    'fonts.googleapis.com',
    'fonts.gstatic.com',
    'stackpath.bootstrapcdn.com',
    'maxcdn.bootstrapcdn.com'
  ];
  
  return allowedDomains.some(domain => url.includes(domain));
}

// Handle messages from client
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[Service Worker] Skipping waiting...');
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    console.log('[Service Worker] Clearing all caches...');
    event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => caches.delete(cacheName))
        );
      }).then(() => {
        console.log('[Service Worker] All caches cleared');
        // Notify clients
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({ type: 'CACHE_CLEARED' });
          });
        });
      })
    );
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

// Background sync (for future use)
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

async function syncData() {
  console.log('[Service Worker] Syncing offline data...');
  // Implement your sync logic here
  try {
    // Example: sync offline form submissions
    const cache = await caches.open(CACHE_NAME);
    // Add your sync logic
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
  }
}

// Push notifications (for future use)
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received');
  
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'FUTO BME Notification';
  const options = {
    body: data.body || 'You have a new notification',
    icon: 'https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg',
    badge: 'https://res.cloudinary.com/dasmnlwnm/image/upload/v1760695706/logo_yjajyk.jpg',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/',
      dateOfArrival: Date.now()
    },
    actions: [
      {
        action: 'open',
        title: 'Open'
      },
      {
        action: 'close',
        title: 'Close'
      }
    ],
    requireInteraction: false,
    tag: 'futo-bme-notification'
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event.action);
  
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Check if there's already a window open
        for (let client of windowClients) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // If not, open a new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Periodic background sync (for future use)
self.addEventListener('periodicsync', (event) => {
  console.log('[Service Worker] Periodic sync triggered:', event.tag);
  
  if (event.tag === 'update-content') {
    event.waitUntil(updateContent());
  }
});

async function updateContent() {
  console.log('[Service Worker] Updating cached content...');
  try {
    const cache = await caches.open(CACHE_NAME);
    // Update important resources
    await Promise.allSettled(
      STATIC_CACHE.map(url => fetch(url).then(response => cache.put(url, response)))
    );
    console.log('[Service Worker] Content updated');
  } catch (error) {
    console.error('[Service Worker] Update failed:', error);
  }
}

console.log('[Service Worker] Script loaded successfully');