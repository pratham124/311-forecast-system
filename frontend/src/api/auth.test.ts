import { afterEach, describe, expect, it, vi } from 'vitest';
import { loginUser } from './auth';

describe('auth api', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows a friendly password validation message for 422 responses', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [
              {
                loc: ['body', 'password'],
                msg: 'String should have at least 8 characters',
                type: 'string_too_short',
              },
            ],
          }),
          {
            status: 422,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    );

    await expect(loginUser('planner@example.com', 'short')).rejects.toThrow('Password must be at least 8 characters.');
  });
});
