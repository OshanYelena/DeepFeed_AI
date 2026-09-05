/**
 * Visual treatment for each feed content type, lifted from the design system.
 */
export interface ContentTypeStyle {
  label: string;
  bg: string;
  text: string;
  border: string;
}

const STYLES: Record<string, ContentTypeStyle> = {
  paper: { label: "Paper", bg: "rgba(147,51,234,.2)", text: "#d8b4fe", border: "rgba(147,51,234,.4)" },
  article: { label: "Article", bg: "rgba(59,130,246,.2)", text: "#93c5fd", border: "rgba(59,130,246,.4)" },
  blog: { label: "Blog", bg: "rgba(16,185,129,.18)", text: "#6ee7b7", border: "rgba(16,185,129,.4)" },
  docs: { label: "Docs", bg: "rgba(245,158,11,.18)", text: "#fcd34d", border: "rgba(245,158,11,.4)" },
  news: { label: "News", bg: "rgba(244,63,94,.18)", text: "#fda4af", border: "rgba(244,63,94,.4)" },
};

const FALLBACK: ContentTypeStyle = {
  label: "Item",
  bg: "rgba(148,163,184,.18)",
  text: "#cbd5e1",
  border: "rgba(148,163,184,.35)",
};

export function contentTypeStyle(type: string): ContentTypeStyle {
  const style = STYLES[type?.toLowerCase()];
  if (style) return style;
  return { ...FALLBACK, label: type ? type.charAt(0).toUpperCase() + type.slice(1) : "Item" };
}
