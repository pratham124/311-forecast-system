type GuestPlaceholderPageProps = {
  onBack: () => void;
};

export function GuestPlaceholderPage({ onBack }: GuestPlaceholderPageProps) {
  return (
    <main className="min-h-screen bg-[#f3f4f5] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-5xl flex-col rounded-[32px] border border-dashed border-[rgba(25,58,90,0.18)] bg-white/80 p-6 shadow-[0_18px_60px_rgba(15,23,42,0.08)] backdrop-blur sm:p-10">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-ink">Guest view</h1>
            <p className="mt-2 text-sm text-muted">The public forecast page will be added later.</p>
          </div>
          <button
            type="button"
            onClick={onBack}
            className="inline-flex min-h-11 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
          >
            Back
          </button>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div aria-label="guest placeholder page" className="h-[55vh] w-full rounded-[28px] border border-dashed border-slate-300 bg-transparent" />
        </div>
      </div>
    </main>
  );
}
