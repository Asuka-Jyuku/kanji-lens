import { DOCUMENT, Injectable, inject } from '@angular/core';

import { FileDownload } from '../application/file-download';

/**
 * Adapter: a download through a Blob link, made and used on the device, with no request to
 * any server (CLAUDE.md, "Segurança").
 */
@Injectable()
export class BrowserFileDownload extends FileDownload {
  private readonly document = inject(DOCUMENT);

  save(fileName: string, content: string, mediaType: string): void {
    const url = URL.createObjectURL(new Blob([content], { type: mediaType }));
    const link = this.document.createElement('a');
    link.href = url;
    link.download = fileName;
    link.hidden = true;
    this.document.body.append(link);
    link.click();
    link.remove();
    // Freed after the click has started the download.
    setTimeout(() => URL.revokeObjectURL(url));
  }
}
