interface SeoProps {
  title: string;
  description: string;
  ogImage?: string;
  canonicalUrl?: string;
  type?: "website" | "article";
  publishedTime?: string;
  modifiedTime?: string;
  tags?: string[];
}

const SITE = "https://shifatsanto.dev";
const SITE_TITLE = "Shifat Santo";
const TWITTER_HANDLE = "@oneKn8";

export function buildSeo(props: SeoProps) {
  const {
    title,
    description,
    ogImage = `${SITE}/og/default.png`,
    canonicalUrl,
    type = "website",
    publishedTime,
    modifiedTime,
    tags = [],
  } = props;

  const fullTitle = title === SITE_TITLE ? title : `${title} | ${SITE_TITLE}`;
  const canonical = canonicalUrl || SITE;

  return {
    title: fullTitle,
    description,
    canonical,
    ogImage: ogImage.startsWith("http") ? ogImage : `${SITE}${ogImage}`,
    type,
    publishedTime,
    modifiedTime,
    tags,
    twitterHandle: TWITTER_HANDLE,
    siteName: SITE_TITLE,
  };
}

export { SITE, SITE_TITLE, TWITTER_HANDLE };
