import { useState } from 'react';
import { FeedbackApiError, submitFeedbackSubmission } from '../../../api/feedbackSubmissions';
import type {
  FeedbackSubmissionCreateResponse,
  FeedbackSubmissionFieldErrors,
  FeedbackSubmissionField,
  ReportType,
} from '../../../types/feedbackSubmissions';

export type FeedbackFormValues = {
  reportType: '' | ReportType;
  description: string;
  contactEmail: string;
};

const INITIAL_VALUES: FeedbackFormValues = {
  reportType: '',
  description: '',
  contactEmail: '',
};

function validate(values: FeedbackFormValues): FeedbackSubmissionFieldErrors {
  const errors: FeedbackSubmissionFieldErrors = {};
  if (!values.reportType) {
    errors.reportType = 'Choose whether you are sending feedback or a bug report.';
  }
  if (!values.description.trim()) {
    errors.description = 'Describe the feedback or issue before submitting.';
  }
  const email = values.contactEmail.trim();
  if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    errors.contactEmail = 'Enter a valid contact email or leave it blank.';
  }
  return errors;
}

export function useFeedbackSubmission() {
  const [values, setValues] = useState<FeedbackFormValues>(INITIAL_VALUES);
  const [errors, setErrors] = useState<FeedbackSubmissionFieldErrors>({});
  const [result, setResult] = useState<FeedbackSubmissionCreateResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const setFieldValue = (field: keyof FeedbackFormValues, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => {
      if (!current[field as FeedbackSubmissionField]) {
        return current;
      }
      const next = { ...current };
      delete next[field as FeedbackSubmissionField];
      return next;
    });
  };

  const submit = async (): Promise<boolean> => {
    const nextErrors = validate(values);
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setResult(null);
      return false;
    }

    setIsSubmitting(true);
    setErrors({});
    try {
      const response = await submitFeedbackSubmission({
        reportType: values.reportType as ReportType,
        description: values.description.trim(),
        contactEmail: values.contactEmail.trim() || null,
      });
      setResult(response);
      setIsSubmitting(false);
      return true;
    } catch (error) {
      if (error instanceof FeedbackApiError) {
        setErrors({
          ...error.fieldErrors,
          ...(Object.keys(error.fieldErrors).length > 0 ? {} : { form: error.message }),
        });
      } else {
        setErrors({ form: error instanceof Error ? error.message : 'Feedback submission failed.' });
      }
      setResult(null);
      setIsSubmitting(false);
      return false;
    }
  };

  const reset = () => {
    setValues(INITIAL_VALUES);
    setErrors({});
    setResult(null);
  };

  return {
    values,
    errors,
    result,
    isSubmitting,
    setFieldValue,
    submit,
    reset,
  };
}
