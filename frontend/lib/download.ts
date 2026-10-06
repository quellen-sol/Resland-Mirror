/** The file name a Content-Disposition header asks for, or `fallback` when
 *  there's no header or no usable name. Directory parts are dropped. */
export function filenameFromContentDisposition(
  header: string | null,
  fallback: string,
): string {
  throw new Error("not implemented");
}
