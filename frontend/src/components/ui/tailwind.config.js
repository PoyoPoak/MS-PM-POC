module.exports = {
  // ...

  theme: {
    extend: {
      colors: {
        brand: {
          50: "rgb(232 244 248)",
          100: "rgb(212 235 245)",
          200: "rgb(184 223 240)",
          300: "rgb(142 204 235)",
          400: "rgb(105 179 227)",
          500: "rgb(74 144 226)",
          600: "rgb(58 123 200)",
          700: "rgb(47 102 173)",
          800: "rgb(37 81 145)",
          900: "rgb(29 63 117)",
        },
        neutral: {
          0: "rgb(255 255 255)",
          50: "rgb(250 251 252)",
          100: "rgb(245 247 249)",
          200: "rgb(238 241 244)",
          300: "rgb(225 232 237)",
          400: "rgb(204 214 221)",
          500: "rgb(168 184 196)",
          600: "rgb(122 140 153)",
          700: "rgb(90 108 122)",
          800: "rgb(61 78 92)",
          900: "rgb(44 62 80)",
          950: "rgb(26 37 48)",
        },
        error: {
          50: "rgb(255 229 229)",
          100: "rgb(255 212 212)",
          200: "rgb(255 194 194)",
          300: "rgb(255 168 168)",
          400: "rgb(255 138 138)",
          500: "rgb(255 107 107)",
          600: "rgb(232 85 85)",
          700: "rgb(207 68 68)",
          800: "rgb(179 53 53)",
          900: "rgb(143 40 40)",
        },
        success: {
          50: "rgb(232 248 245)",
          100: "rgb(209 241 234)",
          200: "rgb(181 233 221)",
          300: "rgb(143 222 201)",
          400: "rgb(107 211 186)",
          500: "rgb(72 201 176)",
          600: "rgb(58 179 152)",
          700: "rgb(47 154 127)",
          800: "rgb(37 128 103)",
          900: "rgb(29 102 83)",
        },
        warning: {
          50: "rgb(255 243 224)",
          100: "rgb(255 232 200)",
          200: "rgb(255 220 171)",
          300: "rgb(255 205 133)",
          400: "rgb(255 194 102)",
          500: "rgb(255 184 77)",
          600: "rgb(245 166 50)",
          700: "rgb(224 143 31)",
          800: "rgb(197 120 21)",
          900: "rgb(164 98 13)",
        },
        "brand-primary": "rgb(58 123 200)",
        "default-font": "rgb(44 62 80)",
        "subtext-color": "rgb(168 184 196)",
        "neutral-border": "rgb(238 241 244)",
        black: "rgb(255 255 255)",
        "default-background": "rgb(255 255 255)",
      },
      fontSize: {
        caption: [
          "12px",
          {
            lineHeight: "16px",
            fontWeight: "400",
            letterSpacing: "0em",
          },
        ],
        "caption-bold": [
          "12px",
          {
            lineHeight: "16px",
            fontWeight: "600",
            letterSpacing: "0em",
          },
        ],
        body: [
          "14px",
          {
            lineHeight: "20px",
            fontWeight: "400",
            letterSpacing: "0em",
          },
        ],
        "body-bold": [
          "14px",
          {
            lineHeight: "20px",
            fontWeight: "600",
            letterSpacing: "0em",
          },
        ],
        "heading-3": [
          "16px",
          {
            lineHeight: "20px",
            fontWeight: "700",
            letterSpacing: "0em",
          },
        ],
        "heading-2": [
          "20px",
          {
            lineHeight: "24px",
            fontWeight: "700",
            letterSpacing: "0em",
          },
        ],
        "heading-1": [
          "30px",
          {
            lineHeight: "36px",
            fontWeight: "700",
            letterSpacing: "0em",
          },
        ],
        "monospace-body": [
          "14px",
          {
            lineHeight: "20px",
            fontWeight: "400",
            letterSpacing: "0em",
          },
        ],
      },
      fontFamily: {
        caption: "Nunito",
        "caption-bold": "Nunito",
        body: "Nunito",
        "body-bold": "Nunito",
        "heading-3": "Nunito",
        "heading-2": "Nunito",
        "heading-1": "Nunito",
        "monospace-body": "monospace",
      },
      boxShadow: {
        sm: "0px 1px 3px 0px rgb(0 0 0 / 0.04)",
        default: "0px 1px 3px 0px rgb(0 0 0 / 0.04)",
        md: "0px 4px 12px -2px rgb(0 0 0 / 0.04), 0px 2px 6px -1px rgb(0 0 0 / 0.03)",
        lg: "0px 8px 24px -4px rgb(0 0 0 / 0.05), 0px 4px 12px -2px rgb(0 0 0 / 0.03)",
        overlay:
          "0px 8px 24px -4px rgb(0 0 0 / 0.05), 0px 4px 12px -2px rgb(0 0 0 / 0.03)",
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        DEFAULT: "6px",
        lg: "8px",
        full: "9999px",
      },
      container: {
        padding: {
          DEFAULT: "16px",
          sm: "calc((100vw + 16px - 640px) / 2)",
          md: "calc((100vw + 16px - 768px) / 2)",
          lg: "calc((100vw + 16px - 1024px) / 2)",
          xl: "calc((100vw + 16px - 1280px) / 2)",
          "2xl": "calc((100vw + 16px - 1536px) / 2)",
        },
      },
      spacing: {
        112: "28rem",
        144: "36rem",
        192: "48rem",
        256: "64rem",
        320: "80rem",
      },
      screens: {
        mobile: {
          max: "767px",
        },
      },
    },
  },
};
