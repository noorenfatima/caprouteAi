import React from 'react';

export default function PageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-white min-h-screen p-8">
      <div className="max-w-7xl mx-auto">{children}</div>
    </div>
  );
}
