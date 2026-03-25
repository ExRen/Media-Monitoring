/**
 * Tempo.co News Crawler using PlaywrightCrawler
 * 
 * Uses browser rendering to handle JavaScript-rendered content
 */

import { PlaywrightCrawler, Dataset, LogLevel, log } from 'crawlee';
import { PAGE_LABELS, type NewsArticle } from './types.js';
import { parseDate, isAfterDate, cleanText, getCurrentTimestamp, extractSource } from './utils.js';

// Configuration
const CONFIG = {
    startUrls: [
        {
            url: 'https://www.tempo.co/',
            label: PAGE_LABELS.LIST,
        },
    ],
    limits: {
        maxRequestsPerCrawl: 50, // Reduced for browser crawling
        maxConcurrency: 2, // Lower concurrency for browser
    },
    dateAfter: new Date('2025-01-01'),
};

const DATASET_NAME = 'news_dataset';

// URL pattern for articles
const ARTICLE_URL_PATTERN = /tempo\.co\/(politik|hukum|ekonomi|lingkungan|wawancara|investigasi|cekfakta|tokoh|foto|hiburan|sepakbola|teroka|kolom|gaya|otomotif|tekno|travel|metro|nasional|dunia|bisnis|bola|seleb|lifestyle|video|infografis|mingguan|plus)\/.+-\d+/;

async function main() {
    log.setLevel(LogLevel.INFO);
    log.info('Starting Tempo.co News Crawler (Playwright)');
    log.info(`Max requests: ${CONFIG.limits.maxRequestsPerCrawl}, Concurrency: ${CONFIG.limits.maxConcurrency}`);

    const crawler = new PlaywrightCrawler({
        maxRequestsPerCrawl: CONFIG.limits.maxRequestsPerCrawl,
        maxConcurrency: CONFIG.limits.maxConcurrency,

        // Browser options
        headless: true,

        // Request timeout
        requestHandlerTimeoutSecs: 120,
        navigationTimeoutSecs: 60,

        async requestHandler({ page, request, enqueueLinks, log }) {
            const label = request.label || PAGE_LABELS.LIST;

            if (label === PAGE_LABELS.LIST) {
                log.info(`Processing LIST page: ${request.url}`);

                // Wait for page to load
                await page.waitForLoadState('networkidle');

                // Extract all links from the page
                const links = await page.evaluate(() => {
                    const anchors = document.querySelectorAll('a[href]');
                    return Array.from(anchors).map(a => a.getAttribute('href') || '');
                });

                // Filter to article URLs
                const articleLinks = links.filter(href => {
                    const pattern = /tempo\.co\/(politik|hukum|ekonomi|lingkungan|wawancara|investigasi|cekfakta|tokoh|foto|hiburan|sepakbola|teroka|kolom|gaya|otomotif|tekno|travel|metro|nasional|dunia|bisnis|bola|seleb|lifestyle|video|infografis|mingguan|plus)\/.+-\d+/;
                    return pattern.test(href);
                });

                const uniqueLinks = [...new Set(articleLinks)];
                log.info(`Found ${uniqueLinks.length} article links`);

                // Log some examples
                uniqueLinks.slice(0, 3).forEach(link => log.info(`  -> ${link}`));

                // Enqueue article pages
                if (uniqueLinks.length > 0) {
                    await enqueueLinks({
                        urls: uniqueLinks,
                        label: PAGE_LABELS.DETAIL,
                    });
                }

            } else if (label === PAGE_LABELS.DETAIL) {
                log.info(`Processing DETAIL page: ${request.url}`);

                // Wait for content to load
                await page.waitForLoadState('networkidle');

                // Extract article data
                const articleData = await page.evaluate(() => {
                    const title = document.querySelector('h1')?.textContent?.trim() || '';
                    const author = document.querySelector('a[href*="/penulis/"]')?.textContent?.trim() || null;
                    const timeEl = document.querySelector('time');
                    const datetime = timeEl?.getAttribute('datetime') || '';

                    // Get all paragraphs
                    const paragraphs: string[] = [];
                    document.querySelectorAll('article p, main p, .detail-konten p').forEach(p => {
                        const text = p.textContent?.trim();
                        if (text && text.length > 20) {
                            paragraphs.push(text);
                        }
                    });

                    return {
                        title,
                        author,
                        datetime,
                        content: paragraphs.join('\n'),
                    };
                });

                // Validate title
                if (!articleData.title) {
                    log.warning(`No title found for ${request.url}`);
                    return;
                }

                // Parse and validate date
                const publishedDate = parseDate(articleData.datetime);
                if (!isAfterDate(publishedDate, CONFIG.dateAfter)) {
                    log.info(`Article date before ${CONFIG.dateAfter.toISOString()}, skipping`);
                    return;
                }

                // Validate content
                if (!articleData.content) {
                    log.warning(`Empty content for ${request.url}`);
                    return;
                }

                // Build article object
                const article: NewsArticle = {
                    url: request.url,
                    title: cleanText(articleData.title),
                    author: articleData.author,
                    published_date: publishedDate?.toISOString() || '',
                    content: articleData.content,
                    scraped_at: getCurrentTimestamp(),
                    source: extractSource(request.url),
                };

                log.info(`✓ Scraped: ${article.title.substring(0, 50)}...`);

                // Save to dataset
                const dataset = await Dataset.open(DATASET_NAME);
                await dataset.pushData(article);
            }
        },

        failedRequestHandler: async ({ request, error }) => {
            const err = error as Error;
            log.error(`Failed: ${request.url} - ${err?.message || 'Unknown error'}`);
        },
    });

    // Add start URLs
    await crawler.addRequests(
        CONFIG.startUrls.map(({ url, label }) => ({
            url,
            label,
        }))
    );

    // Run the crawler
    await crawler.run();

    log.info('Crawler finished!');
    log.info(`Results saved to: storage/datasets/${DATASET_NAME}/`);
}

main().catch(console.error);
