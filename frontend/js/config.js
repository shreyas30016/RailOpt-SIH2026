/**
 * RailOpt Runtime Configuration
 * Resolves the backend API base URL for both local and production environments.
 *
 * Priority order:
 * 1. window.__RAILOPT_CONFIG__?.API_BASE_URL (Injected global configuration object)
 * 2. <meta name="railopt-api-base" content="..."> (HTML meta tag injection)
 * 3. localStorage.getItem("railopt_api_base_url") (Developer/User override in browser)
 * 4. "" (Empty string -> relative paths for same-origin or reverse-proxied hosting)
 */
export function getApiBaseUrl() {
    if (typeof window !== "undefined") {
        if (window.__RAILOPT_CONFIG__ && window.__RAILOPT_CONFIG__.API_BASE_URL) {
            return window.__RAILOPT_CONFIG__.API_BASE_URL.replace(/\/+$/, "");
        }
        const metaTag = document.querySelector('meta[name="railopt-api-base"]');
        if (metaTag && metaTag.getAttribute("content")) {
            return (metaTag.getAttribute("content") || "").replace(/\/+$/, "");
        }
        try {
            const stored = localStorage.getItem("railopt_api_base_url");
            if (stored) return stored.replace(/\/+$/, "");
        } catch (e) {}
    }
    return "";
}

// Attach to window for non-module scripts (e.g., login.html)
if (typeof window !== "undefined") {
    window.getRailOptApiBaseUrl = getApiBaseUrl;
}
