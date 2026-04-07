import type { GuideSection } from '../../types/userGuide';

type UserGuideNavigationProps = {
  sections: GuideSection[];
  activeSectionId: string;
  onSelect: (sectionId: string) => void;
};

export function UserGuideNavigation({ sections, activeSectionId, onSelect }: UserGuideNavigationProps) {
  return (
    <nav aria-label="user guide sections" className="grid gap-2">
      {sections.map((section) => {
        const active = section.sectionId === activeSectionId;
        return (
          <button
            key={section.sectionId}
            type="button"
            onClick={() => onSelect(section.sectionId)}
            className={`rounded-2xl px-4 py-3 text-left text-sm font-semibold transition ${active ? 'bg-ink text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
          >
            {section.label}
          </button>
        );
      })}
    </nav>
  );
}
