import { Alert, AlertDescription, AlertTitle } from '../../../components/ui/alert';

type PublicForecastErrorStateProps = {
  title: string;
  message: string;
};

export function PublicForecastErrorState({ title, message }: PublicForecastErrorStateProps) {
  return (
    <Alert variant="destructive" className="mt-6 rounded-[24px]">
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}
