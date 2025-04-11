import React, { useEffect, useState } from 'react';
import { DeviceInfo } from '../types/websocket'; // Adjust the import path as necessary
import RobotNode from './robot'; // Assuming RobotNode handles styling based on props

interface TrackBoxProps {
  className?: string;
  onCellClick?: (cellNumber: number) => void;
  devices: DeviceInfo[];
}

const TrackBox: React.FC<TrackBoxProps> = ({ className, onCellClick, devices }) => {
  // --- Change state to hold arrays of devices per position ---
  const [robotPositions, setRobotPositions] = useState<Record<number, DeviceInfo[]>>({
    1: [], 2: [], 3: [], 4: [], 5: [],
  });

  useEffect(() => {
    // --- Initialize with empty arrays ---
    const newPositions: Record<number, DeviceInfo[]> = { 1: [], 2: [], 3: [], 4: [], 5: [] };

    devices.forEach(device => {
      // Ensure task is treated as a number for position calculation
      let position = 5; // Default to reserve/loading dock
      if (device.task != null) {
          const taskNum = parseInt(String(device.task), 10);
          if (!isNaN(taskNum) && taskNum >= 1 && taskNum <= 4) {
              position = taskNum;
          }
      }
      // --- Push device into the array for that position ---
      newPositions[position].push(device);
    });

    setRobotPositions(newPositions);
  }, [devices]); // Dependency array remains the same

  // --- Styles remain the same ---
  const containerStyle: React.CSSProperties = {
    padding: '20px',
    display: 'flex',
    gap: '20px',
    alignItems: 'flex-start', // Align items to the start for stacking in cell 5
  };

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gridTemplateRows: '1fr 1fr',
    gap: '10px',
    width: '300px',
    height: '300px',
    maxWidth: '100%',
  };

  const loadingDockStyle: React.CSSProperties = {
    width: '100px',
    minHeight: '100px', // Use minHeight to allow expansion
    display: 'flex',
    flexDirection: 'column', // Stack robots vertically
    justifyContent: 'flex-start', // Align robots to the top
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ccc',
    borderRadius: '4px',
    position: 'relative',
    padding: '5px', // Add some padding
    gap: '5px', // Add gap between stacked robots
  };

  const cellStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '24px',
    fontWeight: 'bold',
    cursor: onCellClick ? 'pointer' : 'default',
    transition: 'background-color 0.2s',
    position: 'relative',
    minHeight: '100px', // Ensure cells have a minimum height
  };

  const cellNumberStyle: React.CSSProperties = {
    position: 'absolute',
    top: '5px',
    left: '5px',
    fontSize: '12px', // Smaller cell number
    color: '#666',
    zIndex: 1,
  };

  const handleCellClick = (cellNumber: number) => {
    if (onCellClick) {
      onCellClick(cellNumber);
    }
  };

  // Helper to render RobotNode, ensuring props are correct
  const renderRobot = (device: DeviceInfo) => (
    <RobotNode
      key={device.id} // Use device ID for key when mapping
      node={{
        id: String(device.id), // Ensure ID is string
        // Determine role based on leader flag
        role: device.leader ? 'leader' : 'follower',
        // Determine status based on missed count
        status: device.missed > 0 ? 'inactive' : 'active',
        task: device.task,
        missed: device.missed
      }}
    />
  );

  return (
    <div className={`track-box ${className || ''}`} style={containerStyle}>
      {/* Main 2x2 grid for positions 1-4 */}
      <div style={gridStyle}>
        {[1, 2, 3, 4].map(cellNumber => (
          <div
            key={cellNumber}
            style={cellStyle}
            onClick={() => handleCellClick(cellNumber)}
          >
            <span style={cellNumberStyle}>{cellNumber}</span>
            {/* --- Map over devices in this position (should ideally be 0 or 1) --- */}
            {robotPositions[cellNumber].map(device => renderRobot(device))}
          </div>
        ))}
      </div>

      {/* Loading dock (position 5) */}
      <div
        style={loadingDockStyle}
        onClick={() => handleCellClick(5)}
      >
        <span style={cellNumberStyle}>5</span>
        {/* --- Map over potentially multiple devices in position 5 --- */}
        {robotPositions[5].map(device => renderRobot(device))}
      </div>
    </div>
  );
};

export default TrackBox;
