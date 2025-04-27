import React from 'react';

// Define the props the Input component will accept, extending standard HTML input attributes
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

// Create the Input component using forwardRef to allow ref passing if needed later
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        // Basic styling - you can customize this further with Tailwind or CSS
        className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
        ref={ref}
        {...props} // Spread the rest of the props (like value, onChange, placeholder)
      />
    );
  }
);
Input.displayName = 'Input'; // Set display name for DevTools

export { Input }; // Export the component