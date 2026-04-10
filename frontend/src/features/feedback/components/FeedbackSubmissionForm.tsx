import type { FeedbackSubmissionFieldErrors } from '../../../types/feedbackSubmissions';
import type { ButtonHTMLAttributes, FormEvent } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../../../components/ui/alert';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select } from '../../../components/ui/select';
import type { FeedbackFormValues } from '../hooks/useFeedbackSubmission';

type FeedbackSubmissionFormProps = {
  values: FeedbackFormValues;
  errors: FeedbackSubmissionFieldErrors;
  isSubmitting: boolean;
  onChange: (field: keyof FeedbackFormValues, value: string) => void;
  onSubmit: () => void;
};

function SubmitButton(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className="inline-flex min-h-12 items-center justify-center rounded-2xl bg-ink px-5 text-sm font-semibold text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
      {...props}
    />
  );
}

export function FeedbackSubmissionForm({
  values,
  errors,
  isSubmitting,
  onChange,
  onSubmit,
}: FeedbackSubmissionFormProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <form className="grid gap-5" onSubmit={handleSubmit}>
      {errors.form ? (
        <Alert variant="destructive">
          <AlertTitle>We couldn't submit your report</AlertTitle>
          <AlertDescription>{errors.form}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-2">
        <Label htmlFor="feedback-report-type">Report type</Label>
        <Select
          id="feedback-report-type"
          aria-invalid={Boolean(errors.reportType)}
          value={values.reportType}
          onChange={(event) => onChange('reportType', event.target.value)}
        >
          <option value="">Choose one</option>
          <option value="Feedback">Feedback</option>
          <option value="Bug Report">Bug Report</option>
        </Select>
        {errors.reportType ? <p className="text-sm font-medium text-red-700">{errors.reportType}</p> : null}
      </div>

      <div className="grid gap-2">
        <Label htmlFor="feedback-description">Details</Label>
        <textarea
          id="feedback-description"
          aria-invalid={Boolean(errors.description)}
          value={values.description}
          onChange={(event) => onChange('description', event.target.value)}
          placeholder="Describe what happened, what you expected, and anything else the team should know."
          className="min-h-[180px] rounded-[24px] border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-sm text-ink shadow-sm outline-none transition placeholder:text-muted focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent/20"
        />
        {errors.description ? <p className="text-sm font-medium text-red-700">{errors.description}</p> : null}
      </div>

      <div className="grid gap-2">
        <Label htmlFor="feedback-contact-email">Contact email (optional)</Label>
        <Input
          id="feedback-contact-email"
          type="email"
          aria-invalid={Boolean(errors.contactEmail)}
          value={values.contactEmail}
          onChange={(event) => onChange('contactEmail', event.target.value)}
          placeholder="you@example.com"
        />
        {errors.contactEmail ? <p className="text-sm font-medium text-red-700">{errors.contactEmail}</p> : null}
      </div>

      <SubmitButton
        type="submit"
        disabled={isSubmitting}
        aria-label="Submit feedback"
      >
        {isSubmitting ? 'Submitting...' : 'Submit report'}
      </SubmitButton>
    </form>
  );
}
