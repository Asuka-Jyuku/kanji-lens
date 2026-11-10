import { TestBed } from '@angular/core/testing';

import { BrowserFileDownload } from './browser-file-download';

describe('BrowserFileDownload', () => {
  const { createObjectURL, revokeObjectURL } = URL;

  afterEach(() => {
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;
    vi.restoreAllMocks();
  });

  it('downloads the content through a Blob link on the page, then removes the link', async () => {
    const blobs: Blob[] = [];
    // jsdom has no Blob URLs and does not download: the link is checked when it is clicked.
    URL.createObjectURL = vi.fn((blob: Blob) => {
      blobs.push(blob);
      return 'blob:kanjilens/1';
    });
    URL.revokeObjectURL = vi.fn();
    const clicked: { href: string; download: string; inPage: boolean }[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      clicked.push({ href: this.href, download: this.download, inPage: this.isConnected });
    });

    TestBed.inject(BrowserFileDownload).save('u65e5-correct.json', '{"a":1}', 'application/json');

    expect(clicked).toEqual([
      { href: 'blob:kanjilens/1', download: 'u65e5-correct.json', inPage: true },
    ]);
    expect(blobs[0].type).toBe('application/json');
    expect(await blobs[0].text()).toBe('{"a":1}');
    expect(document.querySelector('a[download]')).toBeNull();
    await new Promise((resolve) => setTimeout(resolve));
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:kanjilens/1');
  });
});
