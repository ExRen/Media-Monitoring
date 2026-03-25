/**
 * Type definitions for News Crawler
 */

export interface NewsArticle {
    url: string;
    title: string;
    author: string | null;
    published_date: string;
    content: string;
    scraped_at: string;
    source: string;
}

export interface CrawlerConfig {
    maxRequestsPerCrawl: number;
    maxConcurrency: number;
    useSessionPool: boolean;
    respectRobotsTxt: boolean;
    dateAfter: Date;
    skipIfEmptyContent: boolean;
}

export interface PageSelectors {
    list: {
        linkSelector: string;
    };
    detail: {
        title: string;
        author: string;
        publishedDate: string;
        content: string;
    };
}

export const PAGE_LABELS = {
    LIST: 'LIST',
    DETAIL: 'DETAIL',
} as const;

export type PageLabel = typeof PAGE_LABELS[keyof typeof PAGE_LABELS];
