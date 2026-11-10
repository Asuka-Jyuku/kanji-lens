/**
 * Port: hands a file to the person, on their own device (ADR 0004). The browser adapter is
 * `BrowserFileDownload`; nothing leaves the device (CLAUDE.md, "Segurança").
 */
export abstract class FileDownload {
  abstract save(fileName: string, content: string, mediaType: string): void;
}
