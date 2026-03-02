"use client";
/*
 * Documentation:
 * Pie Chart — https://app.subframe.com/9301c998f7d7/library?component=Pie+Chart_0654ccc7-054c-4f3a-8e9a-b7c81dd3963c
 */

import React from "react";
import * as SubframeCore from "@subframe/core";
import * as SubframeUtils from "../utils";

interface PieChartRootProps
  extends React.ComponentProps<typeof SubframeCore.PieChart> {
  className?: string;
}

const PieChartRoot = React.forwardRef<
  React.ElementRef<typeof SubframeCore.PieChart>,
  PieChartRootProps
>(function PieChartRoot({ className, ...otherProps }: PieChartRootProps, ref) {
  return (
    <SubframeCore.PieChart
      className={SubframeUtils.twClassNames("h-52 w-52", className)}
      ref={ref}
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

export const PieChart = PieChartRoot;
