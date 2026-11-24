import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md text-[12px] font-medium transition-[color,background-color,border-color,fill,stroke,transform] outline-none focus-visible:ring-1 focus-visible:ring-(--accent) disabled:pointer-events-none disabled:opacity-40 cursor-pointer active:scale-[0.98] [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-(--accent-deep) text-(--text-on-accent) hover:bg-(--accent-deep)/90 shadow-[inset_0_1px_0_0_var(--inset-hl)]",
        secondary:
          "bg-(--bg-surface) text-(--text-primary) border border-(--border-strong) hover:bg-(--bg-hover) shadow-[inset_0_1px_0_0_var(--inset-hl)]",
        ghost:
          "text-(--text-secondary) hover:bg-(--bg-hover) hover:text-(--text-primary)",
        danger:
          "text-(--status-red) hover:bg-(--status-red)/10",
        outline:
          "border border-(--border-strong) text-(--text-secondary) hover:bg-(--bg-hover) hover:text-(--text-primary) shadow-[inset_0_1px_0_0_var(--inset-hl)]",
      },
      size: {
        default: "h-7 px-2.5",
        sm: "h-6 px-2 text-[11.5px]",
        xs: "h-[22px] px-1.5 text-[11px]",
        icon: "h-7 w-7",
        "icon-sm": "h-6 w-6",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, size, asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}
