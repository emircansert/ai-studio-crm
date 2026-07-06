import { Info } from "lucide-react";

const VERTICAL_HELP =
  "Vertical indicates the startup's main industry or functional domain, such as Manufacturing AI, Sales Automation, Supply Chain, HR Tech, or Computer Vision.";

export function VerticalLabel() {
  return (
    <span className="label-with-help">
      Vertical
      <span className="info-popover" tabIndex={0}>
        <Info aria-label="What does Vertical mean?" size={14} />
        <span className="info-popover__content" role="tooltip">
          {VERTICAL_HELP}
        </span>
      </span>
    </span>
  );
}
