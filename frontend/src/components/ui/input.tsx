import * as React from "react";
import { cn } from "../../lib/utils";

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      autoComplete="off"
      spellCheck={false}
      className={cn(
        "h-7 w-full rounded-md border border-(--border-strong) bg-(--bg-surface) px-2.5 text-[12px] text-(--text-primary) placeholder:text-(--text-muted) outline-none focus:border-(--accent) transition-colors selectable",
        className,
      )}
      {...props}
    />
  );
}
