import { toRecognitionRequest } from './recognition-request';

describe('toRecognitionRequest', () => {
  it('sends the mode, the canvas and the strokes as [x, y, t], in the order drawn', () => {
    const request = toRecognitionRequest(
      {
        canvas: { width: 320, height: 300 },
        strokes: [
          [
            { x: 10.5, y: 20, t: 0 },
            { x: 30, y: 40.25, t: 16 },
          ],
          [{ x: 5, y: 6, t: 400 }],
        ],
      },
      'ordered',
    );

    expect(request).toEqual({
      stroke_order_mode: 'ordered',
      canvas: { width: 320, height: 300 },
      strokes: [
        [
          [10.5, 20, 0],
          [30, 40.25, 16],
        ],
        [[5, 6, 400]],
      ],
    });
  });

  it('is plain JSON, with nothing but the three fields the API accepts', () => {
    const request = toRecognitionRequest(
      { canvas: { width: 1, height: 1 }, strokes: [] },
      'unordered',
    );

    expect(JSON.parse(JSON.stringify(request))).toEqual(request);
    expect(Object.keys(request).sort()).toEqual(['canvas', 'stroke_order_mode', 'strokes']);
  });
});
