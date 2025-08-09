import React from 'react';

export function GraphLegend() {
  const legendItems = [
    { color: 'bg-black', label: 'Super Leader', size: 'w-6 h-6' },
    { color: 'bg-blue-500', label: 'Neighborhood Leader', size: 'w-5 h-5', note: 'Same color as neighborhood' },
    { color: 'bg-blue-500', label: 'Device (Active)', size: 'w-4 h-4', note: 'Colored by neighborhood' },
    { color: 'bg-red-500', label: 'Device (Inactive)', size: 'w-4 h-4' },
  ];

  const clusterItems = [
    { color: 'bg-red-200 border-red-400', label: 'Neighborhood 0', style: 'border-2' },
    { color: 'bg-teal-200 border-teal-400', label: 'Neighborhood 1', style: 'border-2' },
    { color: 'bg-blue-200 border-blue-400', label: 'Neighborhood 2', style: 'border-2' },
    { color: 'bg-green-200 border-green-400', label: 'Neighborhood 3', style: 'border-2' },
    { color: 'bg-yellow-200 border-yellow-400', label: 'More...', style: 'border-2' },
  ];

  const linkItems = [
    { color: 'border-gray-400', label: 'Neighborhood Links', style: 'border-2' },
    { color: 'border-red-600', label: 'Council Links', style: 'border-2' },
  ];

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm">
      <h3 className="text-lg font-medium mb-3">Hierarchy Legend</h3>

      {/* Node Types */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-600 mb-2">Node Types</h4>
        <div className="space-y-2">
          {legendItems.map((item) => (
            <div key={item.label} className="flex flex-col">
              <div className="flex items-center">
                <span className={`${item.size || 'w-4 h-4'} rounded-full mr-3 ${item.color}`}></span>
                <span className="text-sm text-gray-700">{item.label}</span>
              </div>
              {item.note && (
                <span className="text-xs text-gray-500 ml-6 mt-1">{item.note}</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Neighborhood Clusters */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-600 mb-2">Neighborhood Clusters</h4>
        <div className="space-y-2">
          {clusterItems.map((item) => (
            <div key={item.label} className="flex items-center">
              <div className={`w-6 h-4 mr-3 rounded ${item.color} ${item.style}`}></div>
              <span className="text-sm text-gray-700">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Link Types */}
      <div>
        <h4 className="text-sm font-medium text-gray-600 mb-2">Link Types</h4>
        <div className="space-y-2">
          {linkItems.map((item) => (
            <div key={item.label} className="flex items-center">
              <div className={`w-6 h-1 mr-3 ${item.color} ${item.style}`}></div>
              <span className="text-sm text-gray-700">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}