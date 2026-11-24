import * as React from "react";
import * as DM from "@radix-ui/react-dropdown-menu";
import { Check } from "lucide-react";
import { cn } from "../../lib/utils";

export const DropdownMenu = DM.Root;
export const DropdownMenuTrigger = DM.Trigger;

export function DropdownMenuContent({
  className,
  sideOffset = 4,
  ...props
}: React.ComponentPropsWithoutRef<typeof DM.Content>) {
  return (
    <DM.Portal>
      <DM.Content
        sideOffset={sideOffset}
        className={cn(
          "elev z-50 min-w-[160px] rounded-lg border border-(--border-strong) bg-(--bg-surface) p-1",
          className,
        )}
        {...props}
      />
    </DM.Portal>
  );
}

export function DropdownMenuItem({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DM.Item>) {
  return (
    <DM.Item
      className={cn(
        "flex cursor-pointer select-none items-center gap-2 rounded px-2 py-1.5 text-[12px] text-(--text-secondary) outline-none data-[highlighted]:bg-(--bg-hover) data-[highlighted]:text-(--text-primary) data-[disabled]:pointer-events-none data-[disabled]:opacity-40",
        className,
      )}
      {...props}
    />
  );
}

export function DropdownMenuCheckboxItem({
  className,
  children,
  checked,
  ...props
}: React.ComponentPropsWithoutRef<typeof DM.CheckboxItem>) {
  return (
    <DM.CheckboxItem
      checked={checked}
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded py-1.5 pl-7 pr-2 text-[12px] text-(--text-secondary) outline-none data-[highlighted]:bg-(--bg-hover) data-[highlighted]:text-(--text-primary)",
        className,
      )}
      {...props}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        <DM.ItemIndicator>
          <Check size={12} strokeWidth={2} className="text-(--accent)" />
        </DM.ItemIndicator>
      </span>
      {children}
    </DM.CheckboxItem>
  );
}

export function DropdownMenuSeparator({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DM.Separator>) {
  return (
    <DM.Separator
      className={cn("mx-1 my-1 h-px bg-(--border-hairline)", className)}
      {...props}
    />
  );
}

export function DropdownMenuLabel({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DM.Label>) {
  return (
    <DM.Label
      className={cn(
        "px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-(--text-muted)",
        className,
      )}
      {...props}
    />
  );
}
