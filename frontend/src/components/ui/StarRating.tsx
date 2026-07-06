"use client";

import { Star } from "lucide-react";
import { useState } from "react";

type StarRatingProps = {
  /** Current value, 0-5. Fractions supported in read-only mode. */
  value: number | null | undefined;
  /** When provided, the widget becomes interactive (click-to-rate 1-5). */
  onChange?: (value: number) => void;
  size?: number;
  ariaLabel?: string;
  disabled?: boolean;
};

export function StarRating({ value, onChange, size = 18, ariaLabel = "Rating", disabled = false }: StarRatingProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const interactive = Boolean(onChange) && !disabled;
  const displayValue = interactive && hovered !== null ? hovered : value ?? 0;

  if (!interactive) {
    return (
      <span aria-label={`${ariaLabel}: ${value != null ? displayValue.toFixed(1) : "not rated"} of 5`} className="star-rating" role="img">
        {[1, 2, 3, 4, 5].map((position) => {
          const fillRatio = Math.max(0, Math.min(1, displayValue - (position - 1)));
          return (
            <span className="star-rating__star" key={position} style={{ width: size, height: size }}>
              <Star className="star-rating__base" size={size} />
              <span className="star-rating__fill" style={{ width: `${fillRatio * 100}%` }}>
                <Star size={size} />
              </span>
            </span>
          );
        })}
      </span>
    );
  }

  return (
    <span className="star-rating star-rating--interactive" onMouseLeave={() => setHovered(null)} role="radiogroup" aria-label={ariaLabel}>
      {[1, 2, 3, 4, 5].map((position) => {
        const active = displayValue >= position;
        return (
          <button
            aria-checked={value === position}
            aria-label={`${ariaLabel}: ${position} of 5 stars`}
            className={`star-rating__button ${active ? "star-rating__button--active" : ""}`}
            key={position}
            onClick={() => onChange?.(position)}
            onFocus={() => setHovered(position)}
            onBlur={() => setHovered(null)}
            onMouseEnter={() => setHovered(position)}
            role="radio"
            type="button"
          >
            <Star fill={active ? "currentColor" : "none"} size={size} />
          </button>
        );
      })}
    </span>
  );
}
