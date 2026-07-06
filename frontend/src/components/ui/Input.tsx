import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: ReactNode;
  helperText?: string;
};

export function Input({ label, helperText, className = "", ...props }: InputProps) {
  return (
    <label className="field">
      {label ? <span>{label}</span> : null}
      <input className={`input ${className}`.trim()} {...props} />
      {helperText ? <small>{helperText}</small> : null}
    </label>
  );
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: ReactNode;
  helperText?: string;
};

export function Select({ label, helperText, className = "", children, ...props }: SelectProps) {
  return (
    <label className="field">
      {label ? <span>{label}</span> : null}
      <select className={`input ${className}`.trim()} {...props}>
        {children}
      </select>
      {helperText ? <small>{helperText}</small> : null}
    </label>
  );
}
