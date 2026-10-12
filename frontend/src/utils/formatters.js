/**
 * DispatchLens Data Formatting Helper Utilities
 */

export function formatMcNumber(mc) {
    if (!mc || mc === 0 || mc === '0') return 'N/A';
    const str = String(mc).trim();
    const digits = str.replace(/^MC-?/i, '').replace(/\D/g, '');
    if (!digits || !parseInt(digits, 10)) return 'N/A';
    return `MC-${digits}`;
}

export function formatPhoneNumber(phoneStr) {
    if (!phoneStr) return 'N/A';
    const cleaned = ('' + phoneStr).replace(/\D/g, '');
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
        return `(${cleaned.slice(1,4)}) ${cleaned.slice(4,7)}-${cleaned.slice(7)}`;
    }
    return phoneStr;
}

export function formatLocation(address) {
    if (!address) return 'N/A';
    const city = address.city ? String(address.city).trim() : '';
    const state = address.state ? String(address.state).trim() : '';
    if (city && state) {
        return `${city.toUpperCase()}, ${state.toUpperCase()}`;
    } else if (city) {
        return city.toUpperCase();
    } else if (state) {
        return state.toUpperCase();
    }
    return 'N/A';
}

export function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
