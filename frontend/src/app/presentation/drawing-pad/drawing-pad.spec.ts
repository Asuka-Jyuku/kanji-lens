import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DrawingSession } from '../../application/drawing-session';
import { DrawingPad } from './drawing-pad';

// The canvas sits at (10, 20) on the page and measures 320x320 CSS px. jsdom has no layout,
// so the box is stubbed; it also has no 2D context, so only the capture is tested here.
const BOX = { left: 10, top: 20, width: 320, height: 320 } as DOMRect;

describe('DrawingPad', () => {
  let fixture: ComponentFixture<DrawingPad>;
  let page: HTMLElement;
  let canvas: HTMLCanvasElement;
  let session: DrawingSession;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [DrawingPad] }).compileComponents();
    fixture = TestBed.createComponent(DrawingPad);
    page = fixture.nativeElement as HTMLElement;
    canvas = page.querySelector('canvas') as HTMLCanvasElement;
    canvas.getBoundingClientRect = () => BOX;
    canvas.getContext = (() => null) as typeof canvas.getContext;
    session = TestBed.inject(DrawingSession);
    await fixture.whenStable();
  });

  function pointer(type: string, clientX: number, clientY: number, extra: PointerEventInit = {}) {
    canvas.dispatchEvent(
      new PointerEvent(type, {
        pointerId: 1,
        pointerType: 'touch',
        clientX,
        clientY,
        bubbles: true,
        cancelable: true,
        ...extra,
      }),
    );
  }

  function button(name: 'undo' | 'clear'): HTMLButtonElement {
    return page.querySelector(`button.${name}`) as HTMLButtonElement;
  }

  it('turns a pointer stroke into a stroke of canvas points, as drawn', async () => {
    pointer('pointerdown', 50, 60);
    pointer('pointermove', 80, 90);
    pointer('pointermove', 110, 140);
    pointer('pointerup', 110, 140);
    await fixture.whenStable();

    const { canvas: size, strokes } = session.drawing();
    expect(size).toEqual({ width: 320, height: 320 });
    expect(strokes).toHaveLength(1);
    expect(strokes[0].map(({ x, y }) => [x, y])).toEqual([
      [40, 40],
      [70, 70],
      [100, 120],
    ]);
  });

  it('keeps strokes apart, in the order they were drawn', async () => {
    pointer('pointerdown', 20, 30);
    pointer('pointerup', 20, 30);
    pointer('pointerdown', 200, 30);
    pointer('pointermove', 200, 200);
    pointer('pointerup', 200, 200);
    await fixture.whenStable();

    expect(session.drawing().strokes.map((stroke) => stroke.length)).toEqual([1, 2]);
  });

  it('ignores a second finger while the first one draws', async () => {
    pointer('pointerdown', 50, 60);
    pointer('pointerdown', 150, 160, { pointerId: 2 });
    pointer('pointermove', 160, 170, { pointerId: 2 });
    pointer('pointerup', 50, 60);
    await fixture.whenStable();

    expect(session.drawing().strokes).toEqual([[expect.objectContaining({ x: 40, y: 40 })]]);
  });

  it('ignores the right mouse button', async () => {
    pointer('pointerdown', 50, 60, { pointerType: 'mouse', button: 2 });
    await fixture.whenStable();

    expect(session.empty()).toBe(true);
  });

  it('ends the stroke when the pointer is cancelled', async () => {
    pointer('pointerdown', 50, 60);
    pointer('pointercancel', 50, 60);
    pointer('pointermove', 90, 90);
    await fixture.whenStable();

    expect(session.drawing().strokes[0]).toHaveLength(1);
  });

  it('undoes the last stroke and clears everything, with the buttons off when empty', async () => {
    expect(button('undo').disabled).toBe(true);
    expect(button('clear').disabled).toBe(true);

    pointer('pointerdown', 20, 30);
    pointer('pointerup', 20, 30);
    pointer('pointerdown', 40, 50);
    pointer('pointerup', 40, 50);
    await fixture.whenStable();
    expect(button('undo').disabled).toBe(false);

    button('undo').click();
    await fixture.whenStable();
    expect(session.drawing().strokes).toHaveLength(1);

    button('clear').click();
    await fixture.whenStable();
    expect(session.empty()).toBe(true);
    expect(button('clear').disabled).toBe(true);
  });

  it('names the canvas and tells why the drawing stopped growing', async () => {
    expect(canvas.getAttribute('aria-label')).toBe('Área de desenho do kanji');
    for (let i = 0; i <= 40; i++) {
      pointer('pointerdown', 20 + i, 30);
      pointer('pointerup', 20 + i, 30);
    }
    await fixture.whenStable();

    const status = page.querySelector('[role="status"]');
    expect(status?.textContent).toContain('limite de traços');
  });
});
