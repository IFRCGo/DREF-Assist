interface Step {
  label: string;
  active: boolean;
}

const steps: Step[] = [
  { label: "OPERATION OVERVIEW", active: true },
  { label: "EVENT DETAIL", active: false },
  { label: "ACTIONS/NEEDS", active: false },
  { label: "OPERATION", active: false },
  { label: "OPERATIONAL TIMEFRAMES AND CONTACTS", active: false },
];

const StepIndicator = () => {
  return (
    <div className="flex items-center justify-center gap-0 py-6">
      {steps.map((step, index) => (
        <div key={step.label} className="flex items-center">
          <div className="flex flex-col items-center gap-2">
            <div
              className={`flex h-4 w-4 items-center justify-center rounded-full border-2 ${
                step.active
                  ? "border-primary bg-primary"
                  : "border-ifrc-gray bg-card"
              }`}
            >
              {step.active && (
                <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />
              )}
            </div>
            <span
              className={`text-[10px] font-semibold tracking-wide ${
                step.active ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {step.label}
            </span>
          </div>
          {index < steps.length - 1 && (
            <div className="mx-2 mt-[-18px] h-px w-16 bg-border" />
          )}
        </div>
      ))}
    </div>
  );
};

export default StepIndicator;
