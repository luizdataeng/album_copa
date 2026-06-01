const CACHE_NAME = "album-cache-v17";
const STATIC_ASSETS = [
  "/",
  "/manifest.json",
  "/static/styles.css",
  "/static/app.js",
  "/static/flags/placeholder.png",
  "/static/flags/mexico.png",
  "/static/flags/brasil.png",
  "/static/flags/czechia.png",
  "/static/flags/korea.png",
  "/static/flags/south_africa.png",
  "/static/flags/australia.png",
  "/static/flags/bosnia.png",
  "/static/flags/canada.png",
  "/static/flags/haiti.png",
  "/static/flags/morocco.png",
  "/static/flags/paraguay.png",
  "/static/flags/qatar.png",
  "/static/flags/scotland.png",
  "/static/flags/switzerland.png",
  "/static/flags/turkey.png",
  "/static/flags/usa.png",
  "/static/flags/curacao.png",
  "/static/flags/cote.png",
  "/static/flags/ecuador.png",
  "/static/flags/germany.png",
  "/static/flags/coca_cola.png",
  "/static/flags/fwc.png",
  "/static/flags/ghana.png",
  "/static/flags/iraq.png",
  "/static/flags/iran.png",
  "/static/flags/japan.png",
  "/static/flags/jordan.png",
  "/static/flags/norway.png",
  "/static/flags/panama.png",
  "/static/flags/portugal.png",
  "/static/flags/saudi_arabia.png",
  "/static/flags/senegal.png",
  "/static/flags/spain.png",
  "/static/flags/netherlands.png",
  "/static/flags/new_zealand.png",
  "/static/flags/sweden.png",
  "/static/flags/tunisia.png",
  "/static/flags/belgium.png",
  "/static/flags/egypt.png",
  "/static/flags/france.png",
  "/static/flags/argentina.png",
  "/static/flags/algeria.png",
  "/static/flags/austria.png",
  "/static/flags/cabo_verde.png",
  "/static/flags/colombia.png",
  "/static/flags/congo.png",
  "/static/flags/croatia.png",
  "/static/flags/england.png",
  "/static/flags/uruguay.png",
  "/static/flags/uzbekistan.png",
  "/static/icons/icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => (key === CACHE_NAME ? null : caches.delete(key))))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.pathname.startsWith("/album")) return;

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
        return response;
      });
    })
  );
});
