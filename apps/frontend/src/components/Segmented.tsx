export function Segmented({ options, value, onChange }: { options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex p-[3px] rounded-lg bg-surface">
      {options.map((opt) => {
        const active = opt.toLowerCase() === value.toLowerCase();
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            className={`flex-1 text-center px-1 py-[7px] rounded-md text-xs font-semibold transition-colors ${
              active ? "bg-surface-hover text-white" : "text-ink-dim hover:text-ink-body"
            }`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
