import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  getFeedbackSubmission,
  listFeedbackSubmissions,
  submitFeedbackSubmission,
} from '../feedbackSubmissions';

const STORAGE_KEY = 'forecast-system-auth-session';
const fetchMock = vi.fn();

function okJson(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  window.localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
  window.localStorage.clear();
});

describe('feedbackSubmissions API', () => {
  it('submits feedback without auth when there is no stored token', async () => {
    fetchMock.mockResolvedValueOnce(
      okJson(
        {
          feedbackSubmissionId: 'fb-1',
          reportType: 'Feedback',
          processingStatus: 'forwarded',
          acceptedAt: '2026-04-10T18:00:00Z',
          userOutcome: 'accepted',
          statusMessage: 'Recorded.',
        },
        201,
      ),
    );

    const result = await submitFeedbackSubmission({
      reportType: 'Feedback',
      description: 'Everything looks good.',
      contactEmail: null,
    });

    expect(result.feedbackSubmissionId).toBe('fb-1');
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(headers.get('Authorization')).toBeNull();
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('retries anonymous-or-authenticated submission after a 401 when a token exists', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'expired-token',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(
        okJson({
          accessToken: 'fresh-token',
          user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
        }),
      )
      .mockResolvedValueOnce(
        okJson(
          {
            feedbackSubmissionId: 'fb-2',
            reportType: 'Bug Report',
            processingStatus: 'forwarded',
            acceptedAt: '2026-04-10T18:05:00Z',
            userOutcome: 'accepted',
            statusMessage: 'Recorded.',
          },
          201,
        ),
      );

    const result = await submitFeedbackSubmission({
      reportType: 'Bug Report',
      description: 'The chart crashes after filtering.',
      contactEmail: 'person@example.com',
    });

    expect(result.feedbackSubmissionId).toBe('fb-2');
    expect(fetchMock).toHaveBeenCalledTimes(3);
    const firstHeaders = (fetchMock.mock.calls[0]?.[1] as RequestInit).headers as Headers;
    const retryHeaders = (fetchMock.mock.calls[2]?.[1] as RequestInit).headers as Headers;
    expect(firstHeaders.get('Authorization')).toBe('Bearer expired-token');
    expect(retryHeaders.get('Authorization')).toBe('Bearer fresh-token');
  });

  it('maps validation details into user-friendly field errors', async () => {
    fetchMock.mockResolvedValueOnce(
      okJson(
        {
          detail: [
            { loc: ['body', 'reportType'], msg: 'Field required', type: 'missing' },
            { loc: ['body', 'description'], msg: 'Description is required', type: 'value_error' },
            { loc: ['body', 'contactEmail'], msg: 'Email is invalid', type: 'value_error' },
          ],
        },
        422,
      ),
    );

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: 'bad-email',
      }),
    ).rejects.toMatchObject({
      status: 422,
      message: 'Choose whether you are sending feedback or a bug report.',
      fieldErrors: {
        reportType: 'Choose whether you are sending feedback or a bug report.',
        description: 'Describe the feedback or issue before submitting.',
        contactEmail: 'Email is invalid',
      },
    });
  });

  it('uses the report-type choice fallback and generic fallback for ignored validation details', async () => {
    fetchMock
      .mockResolvedValueOnce(
        okJson(
          {
            detail: [{ loc: ['body', 'reportType'], msg: 'Must match enum', type: 'literal_error' }],
          },
          422,
        ),
      )
      .mockResolvedValueOnce(
        okJson(
          {
            detail: [{ loc: ['body', 'contactEmail'], type: 'value_error' }],
          },
          422,
        ),
      )
      .mockResolvedValueOnce(
        okJson(
          {
            detail: [
              { loc: ['body', 0], msg: 'Ignore numeric field', type: 'value_error' },
              { loc: ['body', 'unexpectedField'], msg: 'Ignore unknown field', type: 'value_error' },
            ],
          },
          422,
        ),
      );

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: null,
      }),
    ).rejects.toMatchObject({
      status: 422,
      message: 'Choose Feedback or Bug Report.',
      fieldErrors: {
        reportType: 'Choose Feedback or Bug Report.',
      },
    });

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: null,
      }),
    ).rejects.toMatchObject({
      status: 422,
      message: 'Enter a valid contact email or leave it blank.',
      fieldErrors: {
        contactEmail: 'Enter a valid contact email or leave it blank.',
      },
    });

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: null,
      }),
    ).rejects.toMatchObject({
      status: 422,
      message: 'Feedback submission failed with status 422',
      fieldErrors: {},
    });
  });

  it('uses detail strings and non-JSON fallbacks for submission failures', async () => {
    fetchMock
      .mockResolvedValueOnce(okJson({ detail: 'Tracker is offline' }, 503))
      .mockResolvedValueOnce(new Response('not-json', { status: 500 }))
      .mockResolvedValueOnce(new Response('', { status: 401 }));

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: null,
      }),
    ).rejects.toMatchObject({
      status: 503,
      message: 'Tracker is offline',
    });

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: null,
      }),
    ).rejects.toMatchObject({
      status: 500,
      message: 'Feedback submission failed with status 500',
    });

    await expect(
      submitFeedbackSubmission({
        reportType: 'Feedback',
        description: 'Broken.',
        contactEmail: null,
      }),
    ).rejects.toMatchObject({
      status: 401,
      message: 'Feedback submission failed with status 401',
    });
  });

  it('lists feedback submissions with and without filters', async () => {
    fetchMock
      .mockResolvedValueOnce(
        okJson({
          items: [],
        }),
      )
      .mockResolvedValueOnce(
        okJson({
          items: [
            {
              feedbackSubmissionId: 'fb-3',
              reportType: 'Bug Report',
              submitterKind: 'authenticated',
              processingStatus: 'forward_failed',
              submittedAt: '2026-04-10T18:10:00Z',
              triageStatus: 'new',
            },
          ],
        }),
      );

    await listFeedbackSubmissions();
    await listFeedbackSubmissions({
      reportType: 'Bug Report',
      processingStatus: 'forward_failed',
    });

    expect(String(fetchMock.mock.calls[0]?.[0])).toMatch(/\/api\/v1\/feedback-submissions$/);
    expect(String(fetchMock.mock.calls[1]?.[0])).toContain('reportType=Bug+Report');
    expect(String(fetchMock.mock.calls[1]?.[0])).toContain('processingStatus=forward_failed');
  });

  it('retries queue reads after a 401 and surfaces queue failures', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'expired-token',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(
        okJson({
          accessToken: 'fresh-token',
          user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
        }),
      )
      .mockResolvedValueOnce(okJson({ items: [] }))
      .mockResolvedValueOnce(okJson({ detail: 'Queue unavailable' }, 503));

    const listed = await listFeedbackSubmissions({ reportType: 'all', processingStatus: 'all' });
    expect(listed.items).toEqual([]);

    await expect(listFeedbackSubmissions()).rejects.toMatchObject({
      status: 503,
      message: 'Queue unavailable',
    });
  });

  it('loads feedback detail and falls back on detail failures', async () => {
    fetchMock
      .mockResolvedValueOnce(
        okJson({
          feedbackSubmissionId: 'fb-4',
          reportType: 'Feedback',
          description: 'Need more detail',
          submitterKind: 'anonymous',
          processingStatus: 'accepted',
          submittedAt: '2026-04-10T18:15:00Z',
          triageStatus: 'new',
          visibilityStatus: 'visible',
          statusEvents: [{ eventType: 'accepted', recordedAt: '2026-04-10T18:15:00Z' }],
        }),
      )
      .mockResolvedValueOnce(new Response('not-json', { status: 500 }));

    const detail = await getFeedbackSubmission('fb-4');
    expect(detail.feedbackSubmissionId).toBe('fb-4');

    await expect(getFeedbackSubmission('fb-missing')).rejects.toMatchObject({
      status: 500,
      message: 'Feedback detail request failed with status 500',
    });
  });
});
