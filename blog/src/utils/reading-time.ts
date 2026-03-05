import readingTime from "reading-time";

export function getReadingTime(content: string): string {
  const result = readingTime(content);
  return result.text;
}
