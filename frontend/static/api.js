/**
 * Fetch wrapper for API calls.
 */

export async function api(endpoint, options = {}) {
    const response = await fetch(endpoint, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
    }
    return data;
}
