const CACHE_NAME = 'chapa-do-bairro-v1';
const ASSETS = ['/', '/cardapio', '/static/css/style.css', '/static/js/main.js', '/static/img/logo_nav.png'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)).catch(() => null));
});
self.addEventListener('fetch', event => {
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
