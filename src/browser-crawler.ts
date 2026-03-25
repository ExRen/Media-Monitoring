/**
 * Pure Playwright News Crawler for Tempo.co
 * Uses Playwright directly without Crawlee to avoid got-scraping issues
 */

import { chromium, Browser, Page } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

// Configuration
const CONFIG = {
    startUrl: 'https://www.tempo.co/',
    maxArticles: 30,
    dateAfter: new Date('2025-01-01'),
    outputDir: './storage/datasets/news_dataset',
    delay: 2000, // ms between requests
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

// Extract article links from page
async function extractLinks(page: Page): Promise<string[]> {
    // Get all links from the browser
    const links = await page.evaluate(() => {
        const anchors = document.querySelectorAll('a[href]');
        return Array.from(anchors).map(a => a.getAttribute('href') || '');
    });

    // Debug: log all unique links containing tempo.co
    const tempoLinks = links.filter(h => h.includes('tempo.co'));
    console.log(`   Total tempo.co links: ${tempoLinks.length}`);
    console.log(`   Sample links:`);
    tempoLinks.slice(0, 10).forEach(l => console.log(`     - ${l}`));

    // Filter in Node.js context (not in browser)
    const matched = links.filter(href => ARTICLE_URL_PATTERN.test(href));
    console.log(`   Links matching pattern: ${matched.length}`);

    return matched;
}

// Extract article data from page
async function extractArticle(page: Page, url: string): Promise<NewsArticle | null> {
    try {
        const data = await page.evaluate(() => {
            const title = document.querySelector('h1')?.textContent?.trim() || '';
            const author = document.querySelector('a[href*="/penulis/"]')?.textContent?.trim() || null;
            const timeEl = document.querySelector('time');
            const datetime = timeEl?.getAttribute('datetime') || '';

            // Get all paragraphs
            const paragraphs: string[] = [];
            document.querySelectorAll('article p, main p, .content-wrapper p').forEach(p => {
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

        if (!data.title) {
            console.log(`  ⚠ No title found`);
            return null;
        }

        // Parse date
        let publishedDate: Date | null = null;
        if (data.datetime) {
            publishedDate = new Date(data.datetime);
        }

        // Check date filter
        if (!publishedDate || publishedDate < CONFIG.dateAfter) {
            console.log(`  ⚠ Date ${data.datetime} is before filter date`);
            return null;
        }

        if (!data.content) {
            console.log(`  ⚠ No content found`);
            return null;
        }

        return {
            url,
            title: data.title,
            author: data.author,
            published_date: publishedDate.toISOString(),
            content: data.content,
            scraped_at: new Date().toISOString(),
            source: 'tempo.co',
        };
    } catch (error) {
        console.error(`  ✗ Error extracting: ${error}`);
        return null;
    }
}

async function main() {
    console.log('═══════════════════════════════════════════════');
    console.log('       Tempo.co News Crawler (Playwright)       ');
    console.log('═══════════════════════════════════════════════');
    console.log(`Start URL: ${CONFIG.startUrl}`);
    console.log(`Max articles: ${CONFIG.maxArticles}`);
    console.log(`Date filter: After ${CONFIG.dateAfter.toISOString().split('T')[0]}`);
    console.log('───────────────────────────────────────────────');

    ensureDir(CONFIG.outputDir);

    // Launch browser
    console.log('\n📦 Launching browser...');
    const browser: Browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
    const page = await context.newPage();

    try {
        // Navigate to homepage
        console.log(`\n🌐 Navigating to ${CONFIG.startUrl}`);
        await page.goto(CONFIG.startUrl, { waitUntil: 'networkidle', timeout: 60000 });

        // Save screenshot for debugging
        await page.screenshot({ path: './storage/debug_homepage.png' });
        console.log('📸 Screenshot saved to ./storage/debug_homepage.png');

        // Scroll to load more content
        console.log('\n📜 Scrolling to load content...');
        for (let i = 0; i < 5; i++) {
            await page.evaluate(() => window.scrollBy(0, 1000));
            await page.waitForTimeout(1500);
        }

        // Save HTML for debugging
        const html = await page.content();
        fs.writeFileSync('./storage/debug_homepage.html', html);
        console.log('📄 HTML saved to ./storage/debug_homepage.html');

        // Extract article links
        console.log('\n🔗 Extracting article links...');
        const allLinks = await extractLinks(page);
        const uniqueLinks = [...new Set(allLinks)];
        console.log(`   Found ${uniqueLinks.length} unique article links`);

        // Limit to max articles
        const linksToProcess = uniqueLinks.slice(0, CONFIG.maxArticles);
        console.log(`   Processing ${linksToProcess.length} articles`);

        // Process each article
        const articles: NewsArticle[] = [];
        console.log('\n📰 Scraping articles...');

        for (let i = 0; i < linksToProcess.length; i++) {
            const url = linksToProcess[i];
            console.log(`\n[${i + 1}/${linksToProcess.length}] ${url.split('/').pop()}`);

            try {
                await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
                await page.waitForTimeout(500);

                const article = await extractArticle(page, url);
                if (article) {
                    articles.push(article);
                    console.log(`  ✓ ${article.title.substring(0, 50)}...`);

                    // Save immediately
                    const filename = path.join(CONFIG.outputDir, `article_${articles.length}.json`);
                    fs.writeFileSync(filename, JSON.stringify(article, null, 2));
                }
            } catch (error) {
                console.log(`  ✗ Navigation failed: ${error}`);
            }

            // Delay between requests
            await page.waitForTimeout(CONFIG.delay);
        }

        console.log('\n═══════════════════════════════════════════════');
        console.log('                    COMPLETE                    ');
        console.log('═══════════════════════════════════════════════');
        console.log(`Articles scraped: ${articles.length}`);
        console.log(`Output directory: ${CONFIG.outputDir}`);

    } finally {
        await browser.close();
        console.log('\n🔒 Browser closed');
    }
}

main().catch(console.error);
