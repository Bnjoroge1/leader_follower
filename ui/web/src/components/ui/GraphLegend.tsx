import React from 'react';

export function GraphLegend() {
  const legendItems = [
    { color: 'bg-green-500', label: 'Leader (Active)' }, // Match NetworkGraph green
    { color: 'bg-blue-500', label: 'Follower (Active)' }, // Match NetworkGraph blue
    { color: 'bg-red-500', label: 'Inactive' },         // Match NetworkGraph red
  ];

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm">
      <h3 className="text-lg font-medium mb-3">Legend</h3>
      <div className="space-y-2">
        {legendItems.map((item) => (
          <div key={item.label} className="flex items-center">
            <span className={`w-4 h-4 rounded-full mr-2 ${item.color}`}></span>
            <span className="text-sm text-gray-700">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}