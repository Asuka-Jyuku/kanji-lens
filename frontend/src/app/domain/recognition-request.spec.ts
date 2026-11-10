import { Drawing } from './drawing';
import { toRecognitionRequest } from './recognition-request';

describe('toRecognitionRequest', () => {
  it('sends the strokes as drawn, each point as [x, y, t], with the canvas and the mode', () => {
    const drawing: Drawing = {
      canvas: { width: 320, height: 300 },
      strokes: [
        [
          { x: 41.5, y: 30, t: 0 },
          { x: 41, y: 88.25, t: 140 },
        ],
        [{ x: -4, y: 310, t: 410 }],
      ],
    };

    expect(toRecognitionRequest(drawing, 'ordered')).toEqual({
      stroke_order_mode: 'ordered',
      canvas: { width: 320, height: 300 },
      strokes: [
        [
          [41.5, 30, 0],
          [41, 88.25, 140],
        ],
        [[-4, 310, 410]],
      ],
    });
  });
});
