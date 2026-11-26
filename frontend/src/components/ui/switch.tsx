import * as React from "react";
import * as SwitchPrimitive from "@radix-ui/react-switch";
import { cn } from "../../lib/utils";

export function Switch({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      className={cn(
        "inline-flex h-[18px] w-[32px] shrink-0 cursor-pointer items-center rounded-full border border-transparent bg-(--border-strong) transition-colors hover:bg-(--text-muted)/50 disabled:cursor-default disabled:opacity-40 data-[state=checked]:bg-(--accent-deep) data-[state=checked]:hover:bg-(--accent-deep)/90 outline-none focus-visible:ring-1 focus-visible:ring-(--accent)",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb className="pointer-events-none block h-[14px] w-[14px] translate-x-[2px] rounded-full bg-(--text-primary) transition-transform data-[state=checked]:translate-x-[16px] data-[state=checked]:bg-(--text-on-accent)" />
    </SwitchPrimitive.Root>
  );
}
