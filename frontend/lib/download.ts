function basename(name: string): string {
  return name.split(/[\\/]/).pop()?.trim() ?? "";
}

/** The file name a Content-Disposition header asks for, or `fallback` when
 *  there's no header or no usable name. Directory parts are dropped. */
export function filenameFromContentDisposition(
  header: string | null,
  fallback: string,
): string {
  if (!header) return fallback;

  // RFC 5987 `filename*=UTF-8''…` wins over the plain form when present.
  const extended = /filename\*\s*=\s*([^']*)'[^']*'([^;]+)/i.exec(header);
  if (extended) {
    try {
      const name = basename(decodeURIComponent(extended[2].trim()));
      if (name) return name;
    } catch {
      // Malformed percent-encoding: try the plain form instead.
    }
  }

  const plain = /filename\s*=\s*(?:"([^"]*)"|([^;]+))/i.exec(header);
  const name = basename(plain?.[1] ?? plain?.[2] ?? "");
  return name || fallback;
}
