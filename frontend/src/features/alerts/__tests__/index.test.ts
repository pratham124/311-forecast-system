import { describe, expect, it } from 'vitest';
import { AlertReviewPage } from '../index';

describe('alerts index', () => {
  it('re-exports AlertReviewPage', () => {
    expect(AlertReviewPage).toBeTypeOf('function');
  });
});
