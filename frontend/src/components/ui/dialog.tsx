import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";
import { useT } from "../../lib/i18n";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogContent({
  className,
  children,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>) {
  const t = useT();
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="scrim fixed inset-0 z-50 bg-(--bg-scrim) backdrop-blur-[14px] backdrop-saturate-150 data-[state=open]:animate-[scrim-in_220ms_var(--ease-out)] data-[state=closed]:animate-[scrim-out_150ms_ease-in]" />
      <DialogPrimitive.Content
        className={cn(
          "elev fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border border-(--border-strong) bg-(--bg-surface) p-4 outline-none max-h-[calc(100dvh-2rem)] overflow-y-auto overscroll-contain data-[state=open]:animate-[dialog-in_220ms_var(--ease-out)] data-[state=closed]:animate-[dialog-out_150ms_ease-in]",
          className,
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close
          aria-label={t("CLOSE")}
          className="absolute right-3 top-3 rounded-md p-1 text-(--text-muted) hover:bg-(--bg-hover) hover:text-(--text-primary) cursor-pointer"
        >
          <X size={14} strokeWidth={1.75} />
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mb-3 space-y-1", className)} {...props} />;
}

export function DialogTitle({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      className={cn("text-[14px] font-semibold text-(--text-primary)", className)}
      {...props}
    />
  );
}

export function DialogDescription({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      className={cn("text-[12px] text-(--text-secondary)", className)}
      {...props}
    />
  );
}

export function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mt-4 flex justify-end gap-2", className)} {...props} />;
}
