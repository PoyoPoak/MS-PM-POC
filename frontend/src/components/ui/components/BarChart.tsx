"use client";
/*
 * Documentation:
 * Bar Chart — https://app.subframe.com/9301c998f7d7/library?component=Bar+Chart_4d4f30e7-1869-4980-8b96-617df3b37912
 */

import React from "react";
import * as SubframeCore from "@subframe/core";
import * as SubframeUtils from "../utils";

interface BarChartRootProps
  extends React.ComponentProps<typeof SubframeCore.BarChart> {
  stacked?: boolean;
  className?: string;
}

const BarChartRoot = React.forwardRef<
  React.ElementRef<typeof SubframeCore.BarChart>,
  BarChartRootProps
>(function BarChartRoot(
  { stacked = false, className, ...otherProps }: BarChartRootProps,
  ref
) {
  return (
    <SubframeCore.BarChart
      className={SubframeUtils.twClassNames("h-80 w-full", className)}
      ref={ref}
      stacked={stacked}
      colors={[
        "#4a90e2",
        "#b8dff0",
        "#3a7bc8",
        "#8ecceb",
        "#2f66ad",
        "#69b3e3",
      ]}
      {...otherProps}
    />
  );
});

export const BarChart = BarChartRoot;
