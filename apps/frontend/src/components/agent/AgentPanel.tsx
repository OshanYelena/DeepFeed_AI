import { MessageSquareText } from "lucide-react";

/**
 * The mockup's "Research agent" side panel is a live chat with the agent,
 * but the backend has no conversational endpoint (only insights, topic
 * preferences, adaptation events and reflection reports — see agent.py).
 * Rather than fabricating fake chat replies, this keeps the panel's visual
 * shape and points people at the real Agent page instead.
 */
export function AgentPanel({ context }: { context: string }) {
  return (
    <aside className="border-l border-white/[0.08] flex flex-col bg-surface-panel h-screen overflow-hidden">
      <div className="px-5 pt-[18px] pb-[14px] border-b border-white/[0.08] flex items-center justify-between shrink-0">
        <div className="font-semibold text-sm text-ink">Research agent</div>
        <div className="font-mono text-[10.5px] text-ink-faint">CTX · {context}</div>
      </div>
      <div className="flex-1 px-5 py-6 flex flex-col items-center justify-center gap-3 text-center overflow-hidden">
        <MessageSquareText className="w-7 h-7 text-ink-faint" />
        <p className="text-[13px] leading-relaxed text-ink-muted max-w-[220px]">
          Conversational chat isn&apos;t wired up yet. See the{" "}
          <a href="/agent" className="text-accent-purpleText font-semibold hover:text-white">
            Agent
          </a>{" "}
          page for what DeepFeed has learned so far.
        </p>
      </div>
      <div className="mx-4 mb-[18px] px-3 py-2.5 rounded-[10px] border border-accent-purple/30 bg-surface flex items-center gap-2.5 text-sm text-ink-faint shrink-0">
        <span className="flex-1">Ask about your feed… (coming soon)</span>
        <span className="w-[26px] h-[26px] rounded-[7px] bg-brand-gradient shrink-0 opacity-50" />
      </div>
    </aside>
  );
}
