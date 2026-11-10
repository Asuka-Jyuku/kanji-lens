import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DrawingSession } from '../../application/drawing-session';
import { RecognitionGateway } from '../../application/recognition.gateway';
import { ResultStream, ResultStreamHandlers } from '../../application/result-stream';
import type { RecognitionJob, SubmittedJob } from '../../domain/recognition-job';
import { RecognitionError } from '../../domain/recognition-state';
import { RecognitionPanel } from './recognition-panel';

class FakeGateway extends RecognitionGateway {
  answer: () => Promise<SubmittedJob> = async () => ({ jobId: 'job-1', status: 'queued' });

  submit(): Promise<SubmittedJob> {
    return this.answer();
  }

  get(): Promise<RecognitionJob> {
    return new Promise(() => undefined);
  }
}

class FakeStream extends ResultStream {
  handlers: ResultStreamHandlers | null = null;

  open(_jobId: string, handlers: ResultStreamHandlers) {
    this.handlers = handlers;
    return { close: () => undefined };
  }
}

describe('RecognitionPanel', () => {
  let fixture: ComponentFixture<RecognitionPanel>;
  let page: HTMLElement;
  let gateway: FakeGateway;
  let stream: FakeStream;

  beforeEach(async () => {
    gateway = new FakeGateway();
    stream = new FakeStream();
    await TestBed.configureTestingModule({
      imports: [RecognitionPanel],
      providers: [
        { provide: RecognitionGateway, useValue: gateway },
        { provide: ResultStream, useValue: stream },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(RecognitionPanel);
    page = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  const button = () => page.querySelector('button.recognize') as HTMLButtonElement;
  const status = () => page.querySelector('[role="status"]')?.textContent?.trim() ?? '';

  function draw(): void {
    const session = TestBed.inject(DrawingSession);
    session.resize({ width: 320, height: 320 });
    session.startStroke({ x: 10, y: 10, time: 0 });
    session.endStroke();
  }

  async function recognize(): Promise<void> {
    draw();
    await fixture.whenStable();
    button().click();
    await fixture.whenStable();
  }

  it('keeps "Reconhecer" off while the canvas is empty', async () => {
    expect(button().textContent?.trim()).toBe('Reconhecer');
    expect(button().disabled).toBe(true);

    draw();
    await fixture.whenStable();

    expect(button().disabled).toBe(false);
  });

  it('announces each state of the job, and the best candidate in Japanese', async () => {
    await recognize();
    expect(status()).toBe('Na fila');
    expect(button().disabled).toBe(true);

    stream.handlers?.state({ jobId: 'job-1', status: 'processing', strokeOrderMode: 'unordered' });
    await fixture.whenStable();
    expect(status()).toBe('Reconhecendo…');

    stream.handlers?.state({
      jobId: 'job-1',
      status: 'completed',
      strokeOrderMode: 'unordered',
      predictions: [{ kanji: '日', confidence: 0.6 }],
    });
    await fixture.whenStable();
    expect(status()).toBe('Mais provável: 日');
    expect(page.querySelector('[lang="ja"]')?.textContent).toBe('日');
    expect(button().disabled).toBe(false);
  });

  it.each([
    [new RecognitionError('queue_full', 5), 'Muitos desenhos na fila agora. Tente de novo em 5'],
    [new RecognitionError('invalid_drawing'), 'O desenho não foi aceito'],
    [new RecognitionError('drawing_too_large'), 'O desenho ficou grande demais'],
    [new RecognitionError('job_not_found'), 'O resultado expirou'],
    [new RecognitionError('offline'), 'Sem conexão com o servidor'],
    [new RecognitionError('timeout'), 'O servidor demorou demais'],
    [new RecognitionError('unexpected'), 'Algo deu errado'],
  ])('says what went wrong and what to do (%s)', async (error, message) => {
    gateway.answer = () => Promise.reject(error);

    await recognize();

    expect(status()).toContain(message);
  });

  it('says so when the recognition itself fails', async () => {
    await recognize();

    stream.handlers?.state({
      jobId: 'job-1',
      status: 'failed',
      strokeOrderMode: 'unordered',
      failure: 'inference_failed',
    });
    await fixture.whenStable();

    expect(status()).toBe('Não deu para reconhecer este desenho. Tente de novo.');
  });
});
