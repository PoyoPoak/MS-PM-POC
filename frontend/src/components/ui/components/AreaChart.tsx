"use client";
/*
 * Documentation:
 * Area Chart — https://app.subframe.com/9301c998f7d7/library?component=Area+Chart_8aa1e7b3-5db6-4a62-aa49-137ced21a231
 */

import React from "react";
import * as SubframeCore from "@subframe/core";
import * as SubframeUtils from "../utils";

interface AreaChartRootProps
  extends React.ComponentProps<typeof SubframeCore.AreaChart> {
  stacked?: boolean;
  className?: string;
}

const AreaChartRoot = React.forwardRef<
  React.ElementRef<typeof SubframeCore.AreaChart>,
  AreaChartRootProps
>(function AreaChartRoot(
  { stacked = false, className, ...otherProps }: AreaChartRootProps,
  ref
) {
  return (
    <SubframeCore.AreaChart
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

export const AreaChart = AreaChartRoot;
