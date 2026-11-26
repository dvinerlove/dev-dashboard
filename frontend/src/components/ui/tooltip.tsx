import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { cn } from "../../lib/utils";

export const TooltipProvider = TooltipPrimitive.Provider;
export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;

export function TooltipContent({
  className,
  sideOffset = 4,
  ...props
}: React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        sideOffset={sideOffset}
        className={cn(
          "z-50 max-w-[280px] rounded-md border border-(--border-strong) bg-(--bg-surface) px-2 py-1 text-[11px] text-(--text-primary)",
          className,
        )}
        {...props}
      />
    </TooltipPrimitive.Portal>
  );
}

/** Minimal tooltip: <Tip label="..."><button/></Tip>
 *  A string label also becomes the trigger's aria-label —
 *  icon-only buttons get an accessible name. */
export function Tip({
  label,
  children,
  side,
}: {
  label: React.ReactNode;
  children: React.ReactNode;
  side?: "top" | "bottom" | "left" | "right";
}) {
  const el = React.isValidElement(children) ? children : null;
  // aria-label goes only on icon-only triggers — otherwise we clobber visible text (WCAG 2.5.3)
  const hasText =
    el &&
    React.Children.toArray(
      (el.props as { children?: React.ReactNode }).children,
    ).some((c) => typeof c === "string" && c.trim().length > 0);
  const trigger =
    el && typeof label === "string" && !hasText
      ? React.cloneElement(el, {
          "aria-label": label,
        } as Record<string, string>)
      : children;
  // Tooltip.Root always renders — otherwise the label↔null switch changes the node type,
  // React recreates the trigger and kills CSS transitions inside it
  return (
    <Tooltip>
      <TooltipTrigger asChild>{trigger}</TooltipTrigger>
      {label ? <TooltipContent side={side}>{label}</TooltipContent> : null}
    </Tooltip>
  );
}
