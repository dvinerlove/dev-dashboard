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

/** Лаконичный тултип: <Tip label="..."><button/></Tip>
 *  Строковый label дополнительно становится aria-label триггера —
 *  icon-only кнопки получают доступное имя. */
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
  // aria-label ставим только icon-only триггерам — иначе затрём видимый текст (WCAG 2.5.3)
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
  // Tooltip.Root рендерим всегда — иначе label↔null меняет тип узла,
  // React пересоздаёт триггер и убивает CSS-переходы внутри него
  return (
    <Tooltip>
      <TooltipTrigger asChild>{trigger}</TooltipTrigger>
      {label ? <TooltipContent side={side}>{label}</TooltipContent> : null}
    </Tooltip>
  );
}
