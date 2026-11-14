import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { DrawingSession } from '../../application/drawing-session';
import { BrowserFileDownload } from '../drawing-export/browser-file-download';
import { DrawingSample, compactJson, drawingSample } from '../drawing-export/drawing-sample';
import {
  DEFAULT_COLLECTION_KANJI,
  DEFAULT_REPETITIONS,
  MAX_REPETITIONS,
  batchFileName,
  collectionQueue,
  drawingBatch,
  isWriterCode,
  parseKanjiList,
} from './collection-batch';

/** Why the session did not start or end; the template turns it into a message (ADR 0009). */
type SessionProblem = 'writer' | 'kanji' | 'repetitions' | 'pending';

/**
 * "Sessão de coleta": draws the real recognition set (#93) one kanji after another, with the
 * answer key filled in, and downloads the drawings as one batch (#100; docs/MODEL.md,
 * "Desenhos do canvas"). Development builds only (app.dev-tools.ts). While a session runs, the
 * kanji asked for and the buttons stay fixed at the bottom of the screen, so a phone never
 * scrolls between drawing and saving.
 */
@Component({
  selector: 'app-collection-session',
  templateUrl: './collection-session.html',
  styleUrl: './collection-session.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(window:beforeunload)': 'onBeforeUnload($event)' },
})
export class CollectionSession {
  protected readonly session = inject(DrawingSession);
  private readonly download = inject(BrowserFileDownload);

  protected readonly maxRepetitions = MAX_REPETITIONS;
  protected readonly writer = signal('');
  protected readonly kanjiText = signal(DEFAULT_COLLECTION_KANJI);
  protected readonly repetitions = signal(String(DEFAULT_REPETITIONS));
  protected readonly problem = signal<SessionProblem | null>(null);

  /** The kanji to draw, in order; `null` while no session runs. */
  protected readonly queue = signal<readonly string[] | null>(null);
  protected readonly position = signal(0);
  protected readonly samples = signal<readonly DrawingSample[]>([]);
  /** How many of `samples` the last download had. */
  private readonly downloadedCount = signal(0);
  protected readonly downloaded = signal<string | null>(null);

  protected readonly current = computed(() => this.queue()?.[this.position()] ?? null);
  protected readonly finished = computed(() => this.queue() !== null && this.current() === null);
  protected readonly pending = computed(() => this.samples().length - this.downloadedCount());

  protected onWriter(event: Event): void {
    // Phone keyboards start with a capital letter; the code is lowercase.
    this.writer.set((event.target as HTMLInputElement).value.trim().toLowerCase());
  }

  protected onKanji(event: Event): void {
    this.kanjiText.set((event.target as HTMLTextAreaElement).value);
  }

  protected onRepetitions(event: Event): void {
    this.repetitions.set((event.target as HTMLInputElement).value);
  }

  protected onStart(event: Event): void {
    event.preventDefault();
    if (!isWriterCode(this.writer())) {
      this.problem.set('writer');
      return;
    }
    const kanji = parseKanjiList(this.kanjiText());
    if (kanji === null) {
      this.problem.set('kanji');
      return;
    }
    const repetitions = Number(this.repetitions());
    if (!Number.isInteger(repetitions) || repetitions < 1 || repetitions > MAX_REPETITIONS) {
      this.problem.set('repetitions');
      return;
    }
    this.problem.set(null);
    this.queue.set(collectionQueue(kanji, repetitions, Math.random));
    this.position.set(0);
    this.samples.set([]);
    this.downloadedCount.set(0);
    this.downloaded.set(null);
    this.session.clear();
  }

  /** Keeps the drawing on screen as the kanji asked for, drawn in the right order, and moves on. */
  protected saveAndNext(): void {
    const kanji = this.current();
    if (kanji === null || this.session.empty()) {
      return;
    }
    const label = { kanji, stroke_order: 'correct', strokes: [] } as const;
    const sample = drawingSample(this.session.drawing(), this.session.mode(), label, new Date());
    this.samples.update((samples) => [...samples, sample]);
    this.next();
  }

  protected skip(): void {
    if (this.current() !== null) {
      this.next();
    }
  }

  protected downloadBatch(): void {
    const samples = this.samples();
    if (samples.length === 0) {
      return;
    }
    const batch = drawingBatch(this.writer(), samples, new Date());
    const fileName = batchFileName(batch);
    this.download.save(fileName, compactJson(batch), 'application/json');
    this.downloadedCount.set(samples.length);
    this.downloaded.set(fileName);
  }

  /** Ends the session; refused while drawings were not downloaded, so none is lost. */
  protected end(): void {
    if (this.pending() > 0) {
      this.problem.set('pending');
      return;
    }
    this.problem.set(null);
    this.queue.set(null);
    this.session.clear();
  }

  /** Asks the browser to confirm before leaving with drawings not downloaded yet. */
  protected onBeforeUnload(event: BeforeUnloadEvent): void {
    if (this.pending() > 0) {
      event.preventDefault();
    }
  }

  private next(): void {
    this.problem.set(null);
    this.downloaded.set(null);
    this.position.update((position) => position + 1);
    this.session.clear();
  }
}
