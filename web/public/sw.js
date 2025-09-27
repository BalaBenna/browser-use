// This is a basic service worker file.
// You can add caching strategies or other service worker functionality here.

self.addEventListener('install', (event) => {
  console.log('Service worker installing...');
  // Add a simple caching strategy for demonstration
  event.waitUntil(
    caches.open('my-cache').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        // Add other assets you want to cache
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
