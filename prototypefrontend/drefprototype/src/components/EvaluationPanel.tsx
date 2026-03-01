import { useState } from "react";
import { CheckCircle2, XCircle, ChevronDown, Sparkles, Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { EvaluationResult, CriterionResult } from "@/lib/api";

interface EvaluationPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: EvaluationResult | null;
  loading: boolean;
  onRequestImprovement?: (prompt: string) => void;
}

const SECTION_ORDER = [
  "operation_overview",
  "event_detail",
  "actions_needs",
  "operation",
  "operational_timeframe_contacts",
];

function SectionBlock({
  sectionKey,
  section,
  onRequestImprovement,
}: {
  sectionKey: string;
  section: EvaluationResult["section_results"][string];
  onRequestImprovement?: (prompt: string) => void;
}) {
  const [open, setOpen] = useState(section.status === "needs_revision");

  const entries = Object.entries(section.criteria_results);
  const passCount = entries.filter(([, c]) => c.outcome === "accept").length;
  const failCount = entries.filter(([, c]) => c.outcome === "dont_accept").length;
  const isPass = section.status === "accept";

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border border-border bg-card px-4 py-3 text-left hover:bg-muted/50 transition-colors">
        <div className="flex items-center gap-2.5 min-w-0">
          {isPass ? (
            <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
          ) : (
            <XCircle className="h-5 w-5 shrink-0 text-red-500" />
          )}
          <span className="font-semibold text-sm truncate">
            {section.section_display_name}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-muted-foreground">
            {passCount}/{entries.length}
          </span>
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform ${
              open ? "rotate-180" : ""
            }`}
          />
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <div className="mt-1 space-y-0.5 pl-2">
          {entries.map(([criterionId, cr]) => (
            <CriterionRow
              key={criterionId}
              criterion={cr}
              onRequestImprovement={onRequestImprovement}
            />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

function CriterionRow({
  criterion,
  onRequestImprovement,
}: {
  criterion: CriterionResult;
  onRequestImprovement?: (prompt: string) => void;
}) {
  const isPass = criterion.outcome === "accept";

  return (
    <div
      className={`rounded-md border px-3 py-2.5 text-sm ${
        isPass
          ? "border-green-200 bg-green-50/50 dark:border-green-900 dark:bg-green-950/20"
          : "border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20"
      }`}
    >
      <div className="flex items-start gap-2">
        {isPass ? (
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5 text-green-600" />
        ) : (
          <XCircle className="h-4 w-4 shrink-0 mt-0.5 text-red-500" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm leading-snug">{criterion.criterion}</p>
            {criterion.required && (
              <Badge
                variant="outline"
                className="shrink-0 text-[10px] px-1.5 py-0"
              >
                Required
              </Badge>
            )}
          </div>

          {!isPass && (
            <div className="mt-2 space-y-1.5">
              <p className="text-xs text-muted-foreground">
                {criterion.reasoning}
              </p>
              {criterion.guidance && (
                <p className="text-xs text-muted-foreground italic">
                  {criterion.guidance}
                </p>
              )}
              {criterion.improvement_prompt && onRequestImprovement && (
                <button
                  onClick={() =>
                    onRequestImprovement(criterion.improvement_prompt)
                  }
                  className="mt-1 inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/5 px-2.5 py-1 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
                >
                  <Sparkles className="h-3 w-3" />
                  Improve with AI
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function EvaluationPanel({
  open,
  onOpenChange,
  result,
  loading,
  onRequestImprovement,
}: EvaluationPanelProps) {
  if (!result && !loading) return null;

  const totalPass = result
    ? Object.values(result.section_results).reduce(
        (sum, s) =>
          sum +
          Object.values(s.criteria_results).filter(
            (c) => c.outcome === "accept",
          ).length,
        0,
      )
    : 0;

  const totalCriteria = result
    ? Object.values(result.section_results).reduce(
        (sum, s) => sum + Object.keys(s.criteria_results).length,
        0,
      )
    : 0;

  const isAccepted = result?.overall_status === "accepted";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-lg p-0 flex flex-col"
      >
        <SheetHeader className="px-6 pt-6 pb-4 border-b border-border shrink-0">
          <SheetTitle>Application Evaluation</SheetTitle>
          <SheetDescription>
            Quality assessment against IFRC rubric criteria
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="flex-1">
          <div className="px-6 py-4 space-y-4">
            {loading && (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">
                  Evaluating your application...
                </p>
              </div>
            )}

            {result && !loading && (
              <>
                {/* Overall status banner */}
                <div
                  className={`rounded-lg px-4 py-3 ${
                    isAccepted
                      ? "bg-green-50 border border-green-200 dark:bg-green-950/30 dark:border-green-900"
                      : "bg-amber-50 border border-amber-200 dark:bg-amber-950/30 dark:border-amber-900"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isAccepted ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircle className="h-5 w-5 text-amber-600" />
                      )}
                      <span className="font-semibold text-sm">
                        {isAccepted ? "Ready for Submission" : "Needs Revision"}
                      </span>
                    </div>
                    <span className="text-sm font-medium tabular-nums">
                      {totalPass}/{totalCriteria} criteria met
                    </span>
                  </div>
                  {!isAccepted &&
                    result.improvement_suggestions.length > 0 && (
                      <p className="mt-1.5 text-xs text-muted-foreground">
                        {
                          result.improvement_suggestions.filter(
                            (s) => s.priority === 1,
                          ).length
                        }{" "}
                        required improvements remaining
                      </p>
                    )}
                </div>

                {/* Section breakdowns */}
                <div className="space-y-2">
                  {SECTION_ORDER.filter(
                    (key) => key in result.section_results,
                  ).map((sectionKey) => (
                    <SectionBlock
                      key={sectionKey}
                      sectionKey={sectionKey}
                      section={result.section_results[sectionKey]}
                      onRequestImprovement={onRequestImprovement}
                    />
                  ))}
                </div>
              </>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
