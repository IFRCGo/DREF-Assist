import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { EvaluationResult } from "@/lib/api";

interface FinalEvaluationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: EvaluationResult | null;
  loading: boolean;
  onViewDetails: () => void;
  onDone: () => void;
}

export default function FinalEvaluationDialog({
  open,
  onOpenChange,
  result,
  loading,
  onViewDetails,
  onDone,
}: FinalEvaluationDialogProps) {
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

  const passRate = totalCriteria > 0 ? totalPass / totalCriteria : 0;
  const passPercent = Math.round(passRate * 100);
  const isPassing = passRate >= 0.65;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <DialogTitle className="text-base font-medium text-muted-foreground">
              Evaluating your application...
            </DialogTitle>
            <DialogDescription className="sr-only">
              Please wait while we evaluate your DREF application.
            </DialogDescription>
          </div>
        ) : result ? (
          <div className="flex flex-col items-center text-center gap-4 py-4">
            {isPassing ? (
              <CheckCircle2 className="h-14 w-14 text-green-600" />
            ) : (
              <XCircle className="h-14 w-14 text-red-500" />
            )}

            <div>
              <DialogTitle className="text-xl font-bold">
                {isPassing
                  ? "Application Ready for Submission"
                  : "Application Needs More Work"}
              </DialogTitle>
              <DialogDescription className="sr-only">
                {isPassing
                  ? "Your application meets the majority of IFRC quality requirements."
                  : "Your application is missing substantial information and may be rejected."}
              </DialogDescription>
            </div>

            {/* Progress bar */}
            <div className="w-full max-w-xs space-y-1.5">
              <div className="h-3 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isPassing ? "bg-green-500" : "bg-red-500"
                  }`}
                  style={{ width: `${passPercent}%` }}
                />
              </div>
              <p className="text-sm font-medium tabular-nums">
                {passPercent}% &mdash; {totalPass} of {totalCriteria} criteria
                met
              </p>
            </div>

            <p className="text-sm text-muted-foreground max-w-xs">
              {isPassing
                ? "Your application meets the majority of IFRC quality requirements."
                : "Your application is missing substantial information and may be rejected. Review the details to improve it."}
            </p>

            {/* Actions */}
            <div className="flex items-center gap-3 mt-2">
              <button
                onClick={onViewDetails}
                className="rounded border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
              >
                View Details
              </button>
              <button
                onClick={onDone}
                className="rounded bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-opacity"
              >
                Done
              </button>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
