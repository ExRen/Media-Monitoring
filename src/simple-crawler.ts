/**
 * Alternative News Crawler using native fetch + cheerio
 * This avoids the got-scraping library issues in Crawlee
 */

import * as cheerio from 'cheerio';
import * as fs from 'fs';
import * as path from 'path';

// Configuration
const CONFIG = {
    startUrl: 'https://www.tempo.co/',
    maxRequests: 50, // Limit for testing
    dateAfter: new Date('2025-01-01'),
    outputDir: './storage/datasets/news_dataset',
};

// URL pattern for articles
const ARTICLE_URL_PATTERN = /tempo\.co\/(politik|hukum|ekonomi|lingkungan|wawancara|investigasi|cekfakta|tokoh|foto|hiburan|sepakbola|teroka|kolom|gaya|otomotif|tekno|travel|metro|nasional|dunia|bisnis|bola|seleb|lifestyle|video|infografis|mingguan|plus)\/.+-\d+/;

interface NewsArticle {
    url: string;
    title: string;
    author: string | null;
    published_date: string;
    content: string;
    scraped_at: string;
    source: string;
}

// Ensure output directory exists
function ensureDir(dir: string) {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
}

// Fetch page content
async function fetchPage(url: string): Promise<string | null> {
    try {
        console.log(`Fetching: ${url}`);
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            },
        });

        if (!response.ok) {
            console.log(`Failed to fetch ${url}: ${response.status}`);
            return null;
        }

        return await response.text();
    } catch (error) {
        console.error(`Error fetching ${url}:`, error);
        return null;
    }
}

// Extract article links from a page
function extractArticleLinks(html: string): string[] {
    const $ = cheerio.load(html);
    const links: string[] = [];
    const sampleHrefs: string[] = [];

    $('a[href]').each((i, el) => {
        const href = $(el).attr('href');
        if (href) {
            // Collect samples for debugging
            if (sampleHrefs.length < 10 && href.includes('tempo.co')) {
                sampleHrefs.push(href);
            }

            if (ARTICLE_URL_PATTERN.test(href)) {
                links.push(href);
            }
        }
    });

    console.log(`Total anchors on page: ${$('a[href]').length}`);
    console.log(`Sample hrefs with tempo.co:`);
    sampleHrefs.forEach(h => console.log(`  - ${h}`));
    console.log(`Pattern test examples:`);
    sampleHrefs.slice(0, 3).forEach(h => {
        console.log(`  ${h} -> matches: ${ARTICLE_URL_PATTERN.test(h)}`);
    });

    return [...new Set(links)]; // Remove duplicates
}

// Extract article data from detail page
function extractArticle(html: string, url: string): NewsArticle | null {
    const $ = cheerio.load(html);

    // Extract title
    const title = $('h1').first().text().trim();
    if (!title) {
        console.log(`No title found for ${url}`);
        return null;
    }

    // Extract author
    const author = $('a[href*="/penulis/"]').first().text().trim() || null;

    // Extract date from time element
    const timeEl = $('time').first();
    const datetime = timeEl.attr('datetime');
    let publishedDate: Date | null = null;

    if (datetime) {
        publishedDate = new Date(datetime);
    }

    // Check date filter
    if (!publishedDate || publishedDate < CONFIG.dateAfter) {
        console.log(`Article date ${datetime} is before ${CONFIG.dateAfter.toISOString()}, skipping`);
        return null;
    }

    // Extract content
    const paragraphs: string[] = [];
    $('article p, .detail-konten p, .content-artikel p, main p').each((_, el) => {
        const text = $(el).text().trim();
        if (text && text.length > 20) { // Filter short paragraphs
            paragraphs.push(text);
        }
    });
    const content = paragraphs.join('\n');

    if (!content) {
        console.log(`Empty content for ${url}`);
        return null;
    }

    return {
        url,
        title,
        author,
        published_date: publishedDate.toISOString(),
        content,
        scraped_at: new Date().toISOString(),
        source: 'tempo.co',
    };
}

// Main crawler function
async function crawl() {
    console.log('Starting Simple News Crawler');
    console.log(`Start URL: ${CONFIG.startUrl}`);
    console.log(`Max requests: ${CONFIG.maxRequests}`);

    ensureDir(CONFIG.outputDir);

    const visited = new Set<string>();
    const toVisit: string[] = [CONFIG.startUrl];
    const articles: NewsArticle[] = [];
    let requestCount = 0;

    // First, get article links from homepage
    const homepageHtml = await fetchPage(CONFIG.startUrl);
    if (homepageHtml) {
        const links = extractArticleLinks(homepageHtml);
        console.log(`Found ${links.length} article links on homepage`);
        toVisit.push(...links);
    }

    // Process article pages
    while (toVisit.length > 0 && requestCount < CONFIG.maxRequests) {
        const url = toVisit.shift()!;

        if (visited.has(url) || url === CONFIG.startUrl) {
            continue;
        }
        visited.add(url);
        requestCount++;

        // Add delay to be polite
        await new Promise(resolve => setTimeout(resolve, 500));

        const html = await fetchPage(url);
        if (!html) continue;

        const article = extractArticle(html, url);
        if (article) {
            articles.push(article);
            console.log(`✓ Scraped: ${article.title.substring(0, 50)}...`);

            // Save each article immediately
            const filename = path.join(CONFIG.outputDir, `article_${articles.length}.json`);
            fs.writeFileSync(filename, JSON.stringify(article, null, 2));
        }
    }

    console.log('\n=== Crawl Complete ===');
    console.log(`Total requests: ${requestCount}`);
    console.log(`Articles scraped: ${articles.length}`);
    console.log(`Output directory: ${CONFIG.outputDir}`);
}

// Run the crawler
crawl().catch(console.error);
