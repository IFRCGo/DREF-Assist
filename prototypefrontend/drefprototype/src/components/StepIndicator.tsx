const stepLabels = [
    "OPERATION OVERVIEW",
    "EVENT DETAIL",
    "ACTIONS/NEEDS",
    "OPERATION",
    "OPERATIONAL TIMEFRAMES AND CONTACTS",
];

interface StepIndicatorProps {
    activeStep: number;
}

const StepIndicator = ({ activeStep }: StepIndicatorProps) => {
    return (
        <div className="flex items-center justify-between py-6 px-8">
            {stepLabels.map((label, index) => (
                <div key={label} className="flex flex-col items-center gap-2 relative flex-1">
                    <div
                        className={`flex h-4 w-4 items-center justify-center rounded-full border-2 ${
                            index < activeStep
                                ? "border-black bg-black"
                                : index === activeStep
                                    ? "border-primary bg-primary"
                                    : "border-gray-400 bg-gray-400"
                        } relative z-10`}
                    >
                        {index < activeStep ? (
                            <svg className="h-3 w-3 text-white" viewBox="0 0 16 16" fill="none">
                                <path d="M13 4L6 11L3 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                        ) : index === activeStep ? (
                            <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />
                        ) : null}
                    </div>
                    <span
                        className={`text-[10px] font-semibold tracking-wide whitespace-nowrap text-center leading-none ${
                            index === activeStep ? "text-primary" : "text-muted-foreground"
                        }`}
                    >
                        {label}
                    </span>
                    {index < stepLabels.length - 1 && (
                        <div
                            className="absolute left-1/2 top-[6px] h-1 bg-border"
                            style={{
                                width: 'calc(100% - 8px)'
                            }}
                        />
                    )}
                </div>
            ))}
        </div>
    );
};

export default StepIndicator;