/** A UTC timestamp from the API, shown in the browser's time zone and locale. */
export function LocalDate({ iso, showTime = true }: { iso: string; showTime?: boolean }) {
  const options: Intl.DateTimeFormatOptions = showTime
    ? {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }
    : { year: "numeric", month: "short", day: "numeric" };
  return <time dateTime={iso}>{new Date(iso).toLocaleString(undefined, options)}</time>;
}
