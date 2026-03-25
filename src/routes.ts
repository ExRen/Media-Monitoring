/**
 * Route handlers for the news crawler
 */

import { createCheerioRouter, Dataset } from 'crawlee';
import { PAGE_LABELS, type NewsArticle } from './types.js';
import { parseDate, isAfterDate, cleanText, getCurrentTimestamp, extractSource } from './utils.js';

// Configuration
const DATE_THRESHOLD = new Date('2025-01-01');
const DATASET_NAME = 'news_dataset';

// Tempo.co URL patterns - articles have format: /kategori/slug-id (e.g., /ekonomi/article-slug-123456)
// Made more flexible: match any article URL with category and slug ending with numbers
const ARTICLE_URL_PATTERN = /tempo\.co\/(politik|hukum|ekonomi|lingkungan|wawancara|investigasi|cekfakta|tokoh|foto|hiburan|sepakbola|teroka|kolom|gaya|otomotif|tekno|travel|metro|nasional|dunia|bisnis|bola|seleb|lifestyle|video|infografis|mingguan|plus)\/.+-\d+/;

// Selectors - Updated for Tempo.co
const SELECTORS = {
    list: {
        // Tempo.co uses regular anchor tags for article links
        // We'll filter by URL pattern instead of class
        articleLink: 'a[href*="tempo.co"]',
    },
    detail: {
        title: 'h1',
        // Tempo.co author patterns - they use penulis links
        author: 'a[href*="/penulis/"]',
        // Time element or date text
        publishedDate: 'time',
        // Article content paragraphs
        content: 'article p, .detail-konten p, .content-artikel p, main p',
    },
};

export const router = createCheerioRouter();

/**
 * LIST page handler - Extract article links from homepage/category pages
 */
router.addHandler(PAGE_LABELS.LIST, async ({ $, enqueueLinks, log, request }) => {
    log.info(`Processing LIST page: ${request.url}`);

    // Debug: log total links on page
    const totalLinks = $('a[href]').length;
    log.info(`Total links on page: ${totalLinks}`);

    // Find all links and filter to article URLs
    const allLinks: string[] = [];
    let debugSample: string[] = [];

    $('a[href]').each((i, el) => {
        const href = $(el).attr('href');
        if (href) {
            // Debug: collect sample of hrefs
            if (debugSample.length < 5 && href.includes('tempo.co')) {
                debugSample.push(href);
            }

            if (ARTICLE_URL_PATTERN.test(href)) {
                allLinks.push(href);
            }
        }
    });

    // Log sample URLs for debugging
    log.info(`Sample URLs found: ${debugSample.join(' | ')}`);

    // Remove duplicates
    const uniqueLinks = [...new Set(allLinks)];
    log.info(`Found ${uniqueLinks.length} article links matching pattern`);

    // Enqueue article URLs with DETAIL label
    if (uniqueLinks.length > 0) {
        await enqueueLinks({
            urls: uniqueLinks,
            label: PAGE_LABELS.DETAIL,
        });
    }

    // Check for pagination
    const paginationSelectors = [
        'a.next',
        'a[rel="next"]',
        '.pagination a:last-child',
        'a:contains("Selanjutnya")',
        'a:contains("Muat Lebih Banyak")',
    ];

    for (const selector of paginationSelectors) {
        try {
            const nextPage = $(selector).attr('href');
            if (nextPage) {
                log.info(`Found pagination link: ${nextPage}`);
                await enqueueLinks({
                    selector: selector,
                    label: PAGE_LABELS.LIST,
                });
                break;
            }
        } catch {
            // Selector not found, continue
        }
    }
});

/**
 * DETAIL page handler - Extract article content
 */
router.addHandler(PAGE_LABELS.DETAIL, async ({ $, request, log }) => {
    log.info(`Processing DETAIL page: ${request.url}`);

    // Extract title
    const title = cleanText($(SELECTORS.detail.title).first().text());
    if (!title) {
        log.warning(`No title found for ${request.url}, skipping`);
        return;
    }

    // Extract author (optional)
    const author = cleanText($(SELECTORS.detail.author).first().text()) || null;

    // Extract published date from datetime attribute
    const timeElement = $(SELECTORS.detail.publishedDate).first();
    const dateTimeAttr = timeElement.attr('datetime');
    const publishedDate = parseDate(dateTimeAttr);

    // Apply date filter - skip articles before threshold
    if (!isAfterDate(publishedDate, DATE_THRESHOLD)) {
        log.info(`Article date ${dateTimeAttr} is before ${DATE_THRESHOLD.toISOString()}, skipping`);
        return;
    }

    // Extract content - join all paragraphs
    const paragraphs: string[] = [];
    $(SELECTORS.detail.content).each((_, el) => {
        const text = cleanText($(el).text());
        if (text) {
            paragraphs.push(text);
        }
    });
    const content = paragraphs.join('\n');

    // Skip if content is empty
    if (!content) {
        log.warning(`Empty content for ${request.url}, skipping`);
        return;
    }

    // Build article object
    const article: NewsArticle = {
        url: request.url,
        title,
        author,
        published_date: publishedDate?.toISOString() || '',
        content,
        scraped_at: getCurrentTimestamp(),
        source: extractSource(request.url),
    };

    log.info(`Scraped article: ${title}`);

    // Save to dataset
    const dataset = await Dataset.open(DATASET_NAME);
    await dataset.pushData(article);
});

/**
 * Default handler for any unmatched routes
 */
router.addDefaultHandler(async ({ request, log }) => {
    log.warning(`Unhandled route: ${request.url}`);
});
