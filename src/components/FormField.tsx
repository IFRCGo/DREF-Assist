import { ReactNode } from "react";

interface FormFieldProps {
  label: string;
  description?: string;
  children: ReactNode;
  required?: boolean;
}

const FormField = ({ label, description, children, required }: FormFieldProps) => {
  return (
    <div className="rounded border border-border bg-card p-5">
      <div className="flex flex-col gap-4 md:flex-row">
        <div className="md:w-1/3">
          <p className="font-semibold text-foreground text-sm">
            {label}
            {required && <span className="text-primary">*</span>}
          </p>
          {description && (
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {description}
            </p>
          )}
        </div>
        <div className="flex-1">{children}</div>
      </div>
    </div>
  );
};

export default FormField;
