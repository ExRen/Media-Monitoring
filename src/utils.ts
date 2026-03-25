/**
 * Utility functions for the news crawler
 */

/**
 * Parse a date string from various formats
 */
export function parseDate(dateStr: string | null | undefined): Date | null {
    if (!dateStr) return null;

    try {
        // Try parsing ISO format first (datetime attribute)
        const date = new Date(dateStr);
        if (!isNaN(date.getTime())) {
            return date;
        }
        return null;
    } catch {
        return null;
    }
}

/**
 * Check if a date is after the threshold date
 */
export function isAfterDate(date: Date | null, threshold: Date): boolean {
    if (!date) return false;
    return date.getTime() >= threshold.getTime();
}

/**
 * Clean and normalize text content
 */
export function cleanText(text: string | null | undefined): string {
    if (!text) return '';
    return text
        .replace(/\s+/g, ' ')  // Normalize whitespace
        .replace(/\n\s*\n/g, '\n')  // Remove empty lines
        .trim();
}

/**
 * Get current timestamp in ISO format
 */
export function getCurrentTimestamp(): string {
    return new Date().toISOString();
}

/**
 * Extract domain from URL for source field
 */
export function extractSource(url: string): string {
    try {
        const urlObj = new URL(url);
        return urlObj.hostname.replace('www.', '');
    } catch {
        return 'unknown';
    }
}
