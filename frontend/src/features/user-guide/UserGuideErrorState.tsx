type UserGuideErrorStateProps = {
  title: string;
  message: string;
};

export function UserGuideErrorState({ title, message }: UserGuideErrorStateProps) {
  return (
    <section className="mt-6 rounded-[24px] border border-red-200 bg-red-50 px-5 py-6">
      <h2 className="text-lg font-semibold text-red-900">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-red-800">{message}</p>
    </section>
  );
}
