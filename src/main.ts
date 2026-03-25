/**
 * Tempo.co News Crawler for ASABRI articles
 * 
 * Crawls search results from Tempo.co and extracts news articles
 * about ASABRI topic with filtering by date.
 */

import { CheerioCrawler, LogLevel, log } from 'crawlee';
import { router } from './routes.js';
import { PAGE_LABELS } from './types.js';

// Configuration from user requirements
const CONFIG = {
    startUrls: [
        {
            url: 'https://www.tempo.co/',
            label: PAGE_LABELS.LIST,
        },
    ],
    limits: {
        maxRequestsPerCrawl: 300,
        maxConcurrency: 5,
    },
    antiBlocking: {
        useSessionPool: true,
        respectRobotsTxt: true,
        retryOnBlocked: true,
        maxRequestRetries: 3,
    },
};

async function main() {
    log.setLevel(LogLevel.DEBUG);  // Changed to DEBUG for more info
    log.info('Starting Tempo.co ASABRI News Crawler');
    log.info(`Configuration: Max requests=${CONFIG.limits.maxRequestsPerCrawl}, Concurrency=${CONFIG.limits.maxConcurrency}`);

    // Create crawler instance
    const crawler = new CheerioCrawler({
        requestHandler: router,

        // Limits
        maxRequestsPerCrawl: CONFIG.limits.maxRequestsPerCrawl,
        maxConcurrency: CONFIG.limits.maxConcurrency,

        // Simplified configuration - disable session pool for testing
        useSessionPool: false,

        // Retry configuration
        maxRequestRetries: CONFIG.antiBlocking.maxRequestRetries,

        // Request timing - increase timeouts
        requestHandlerTimeoutSecs: 120,
        navigationTimeoutSecs: 120,

        // Be polite
        minConcurrency: 1,

        // Better error handling - log full error
        failedRequestHandler: async ({ request, error }) => {
            const err = error as Error;
            log.error(`Request failed: ${request.url}`);
            log.error(`Error: ${err?.message || 'Unknown error'}`);
            if (err?.stack) {
                log.error(`Stack: ${err.stack}`);
            }
        },
    });

    // Add start URLs with labels
    await crawler.addRequests(
        CONFIG.startUrls.map(({ url, label }) => ({
            url,
            label,
        }))
    );

    // Run the crawler
    log.info('Crawler started...');
    await crawler.run();

    log.info('Crawler finished!');
    log.info('Results saved to: storage/datasets/news_dataset/');
}

// Run the crawler
main().catch((error) => {
    console.error('Crawler failed:', error);
    process.exit(1);
});
