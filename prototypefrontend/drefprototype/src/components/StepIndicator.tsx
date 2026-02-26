const stepLabels = [
  "OPERATION OVERVIEW",
  "EVENT DETAIL",
  "ACTIONS/NEEDS",
  "OPERATION",
  "OPERATIONAL TIMEFRAMES AND CONTACTS",
  "REVIEW & SUBMIT",
];

interface StepIndicatorProps {
  activeStep: number;
}

const StepIndicator = ({ activeStep }: StepIndicatorProps) => {
  return (
    <div className="flex items-center justify-center gap-0 py-6">
      {stepLabels.map((label, index) => (
        <div key={label} className="flex items-center">
          <div className="flex flex-col items-center gap-2">
            <div
              className={`flex h-4 w-4 items-center justify-center rounded-full border-2 ${
                index === activeStep
                  ? "border-primary bg-primary"
                  : "border-ifrc-gray bg-card"
              }`}
            >
              {index === activeStep && (
                <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />
              )}
            </div>
            <span
              className={`text-[10px] font-semibold tracking-wide ${
                index === activeStep ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {label}
            </span>
          </div>
          {index < stepLabels.length - 1 && (
            <div className="mx-2 mt-[-18px] h-px w-16 bg-border" />
          )}
        </div>
      ))}
    </div>
  );
};

export default StepIndicator;
