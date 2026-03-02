"use client";
/*
 * Documentation:
 * Button Key — https://app.subframe.com/9301c998f7d7/library?component=Button+Key_9d5af9fb-cf7d-4952-bbc5-a3d0af2c18ee
 */

import React from "react";
import * as SubframeCore from "@subframe/core";
import * as SubframeUtils from "../utils";

interface ButtonKeyRootProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  disabled?: boolean;
  variant?:
    | "brand-primary"
    | "brand-secondary"
    | "brand-tertiary"
    | "neutral-primary"
    | "neutral-secondary"
    | "neutral-tertiary"
    | "destructive-primary"
    | "destructive-secondary"
    | "destructive-tertiary"
    | "inverse";
  size?: "large" | "medium" | "small";
  children?: React.ReactNode;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  loading?: boolean;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
}

const ButtonKeyRoot = React.forwardRef<HTMLButtonElement, ButtonKeyRootProps>(
  function ButtonKeyRoot(
    {
      disabled = false,
      variant = "brand-primary",
      size = "medium",
      children,
      icon = null,
      iconRight = null,
      loading = false,
      className,
      type = "button",
      ...otherProps
    }: ButtonKeyRootProps,
    ref
  ) {
    return (
      <button
        className={SubframeUtils.twClassNames(
          "group/9d5af9fb flex h-8 cursor-pointer items-center justify-center gap-2 rounded-md border-none bg-brand-600 px-3 text-left transition-all hover:bg-brand-500 hover:transition-all hover:translate-y-[2px] active:bg-brand-600 active:transition-all active:translate-y-[4px] disabled:cursor-default disabled:bg-neutral-200 disabled:transition-all disabled:translate-y-0 hover:disabled:cursor-default hover:disabled:bg-neutral-200 hover:disabled:transition-all hover:disabled:translate-y-0 active:disabled:cursor-default active:disabled:bg-neutral-200 active:disabled:transition-all active:disabled:translate-y-0",
          {
            "h-6 w-auto flex-row flex-nowrap gap-1 px-2 py-0": size === "small",
            "h-10 w-auto px-4 py-0": size === "large",
            "bg-transparent hover:bg-[#ffffff29] active:bg-[#ffffff3d]":
              variant === "inverse",
            "bg-transparent hover:bg-error-50 active:bg-error-100":
              variant === "destructive-tertiary",
            "bg-error-50 hover:bg-error-100 active:bg-error-50":
              variant === "destructive-secondary",
            "bg-error-600 hover:bg-error-500 active:bg-error-600":
              variant === "destructive-primary",
            "bg-transparent hover:bg-neutral-100 active:bg-neutral-200":
              variant === "neutral-tertiary",
            "border border-solid border-neutral-border bg-default-background hover:bg-neutral-50 active:bg-default-background":
              variant === "neutral-secondary",
            "bg-neutral-100 hover:bg-neutral-200 active:bg-neutral-100":
              variant === "neutral-primary",
            "bg-transparent hover:bg-brand-50 active:bg-brand-100":
              variant === "brand-tertiary",
            "bg-brand-50 hover:bg-brand-100 active:bg-brand-50":
              variant === "brand-secondary",
          },
          className
        )}
        ref={ref}
        type={type}
        disabled={disabled}
        {...otherProps}
      >
        {icon ? (
          <SubframeCore.IconWrapper
            className={SubframeUtils.twClassNames(
              "text-body font-body text-black group-disabled/9d5af9fb:text-neutral-400",
              {
                hidden: loading,
                "text-heading-3 font-heading-3": size === "large",
                "text-error-700":
                  variant === "destructive-tertiary" ||
                  variant === "destructive-secondary",
                "text-neutral-700":
                  variant === "neutral-tertiary" ||
                  variant === "neutral-secondary" ||
                  variant === "neutral-primary",
                "text-brand-700":
                  variant === "brand-tertiary" || variant === "brand-secondary",
              }
            )}
          >
            {icon}
          </SubframeCore.IconWrapper>
        ) : null}
        <div
          className={SubframeUtils.twClassNames(
            "hidden h-4 w-4 flex-none items-center justify-center gap-2",
            { flex: loading, "h-3 w-3 flex-none": size === "small" }
          )}
        >
          <SubframeCore.Loader
            className={SubframeUtils.twClassNames(
              "font-['Inter'] text-[12px] font-[400] leading-[20px] text-black group-disabled/9d5af9fb:text-neutral-400",
              {
                "text-caption font-caption": size === "small",
                "text-error-700":
                  variant === "destructive-tertiary" ||
                  variant === "destructive-secondary",
                "text-neutral-700":
                  variant === "neutral-tertiary" ||
                  variant === "neutral-secondary" ||
                  variant === "neutral-primary",
                "text-brand-700":
                  variant === "brand-tertiary" || variant === "brand-secondary",
              }
            )}
          />
        </div>
        {children ? (
          <span
            className={SubframeUtils.twClassNames(
              "whitespace-nowrap text-body-bold font-body-bold text-black group-disabled/9d5af9fb:text-neutral-400",
              {
                hidden: loading,
                "text-caption-bold font-caption-bold": size === "small",
                "text-error-700":
                  variant === "destructive-tertiary" ||
                  variant === "destructive-secondary",
                "text-neutral-700":
                  variant === "neutral-tertiary" ||
                  variant === "neutral-secondary" ||
                  variant === "neutral-primary",
                "text-brand-700":
                  variant === "brand-tertiary" || variant === "brand-secondary",
              }
            )}
          >
            {children}
          </span>
        ) : null}
        {iconRight ? (
          <SubframeCore.IconWrapper
            className={SubframeUtils.twClassNames(
              "text-body font-body text-black group-disabled/9d5af9fb:text-neutral-400",
              {
                "text-heading-3 font-heading-3": size === "large",
                "text-error-700":
                  variant === "destructive-tertiary" ||
                  variant === "destructive-secondary",
                "text-neutral-700":
                  variant === "neutral-tertiary" ||
                  variant === "neutral-secondary" ||
                  variant === "neutral-primary",
                "text-brand-700":
                  variant === "brand-tertiary" || variant === "brand-secondary",
              }
            )}
          >
            {iconRight}
          </SubframeCore.IconWrapper>
        ) : null}
      </button>
    );
  }
);

export const ButtonKey = ButtonKeyRoot;
