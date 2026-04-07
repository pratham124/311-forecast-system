import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { UserGuidePanel } from '../features/user-guide';

export function UserGuideHostPage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
      <Card className="rounded-[30px] border-white/70 bg-white/88 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <CardHeader className="gap-4 pb-4">
          <p className="text-xs uppercase tracking-[0.24em] text-accent">Help</p>
          <CardTitle className="max-w-4xl text-4xl leading-tight text-ink sm:text-5xl">Current user guide</CardTitle>
        </CardHeader>
        <CardContent className="pb-6">
          <UserGuidePanel entryPoint="app_user_guide_page" />
        </CardContent>
      </Card>
    </main>
  );
}
