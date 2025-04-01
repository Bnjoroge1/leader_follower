import React, { useEffect, useState } from 'react';
import { DeviceInfo } from '../types/websocket'; // Adjust the import path as necessary
import RobotNode from './robot';

interface TrackBoxProps {
  className?: string;
  onCellClick?: (cellNumber: number) => void;
  devices: DeviceInfo[];
}

const TrackBox: React.FC<TrackBoxProps> = ({ className, onCellClick, devices }) => {
  const [robotPositions, setRobotPositions] = useState<Record<number, DeviceInfo | null>>({
    1: null,
    2: null,
    3: null,
    4: null,
    5: null,
  });

  useEffect(() => {
    const newPositions: Record<number, DeviceInfo | null> = {1: null, 2: null, 3: null, 4: null, 5: null};

    devices.forEach(device => {
      const position = device.task ? parseInt(device.task) : 5; // 5 is the "sleeping" position
      newPositions[position] = device;
    });

    setRobotPositions(newPositions);
  }, [devices]);

  const containerStyle: React.CSSProperties = {
    padding: '20px',
    display: 'flex',
    gap: '20px',
    alignItems: 'center',
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
    height: '100px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    border: '1px solid #ccc',
    borderRadius: '4px',
    position: 'relative',
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
  };
  
  const cellNumberStyle: React.CSSProperties = {
    position: 'absolute',
    top: '5px',
    left: '5px',
    fontSize: '22px',
    color: '#666',
    zIndex: 1,
  };

  const handleCellClick = (cellNumber: number) => {
    if (onCellClick) {
      onCellClick(cellNumber);
    }
  };

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
            {robotPositions[cellNumber] && (
              <div style={{ position: 'absolute' }}>
                <RobotNode 
                  node={{
                    id: robotPositions[cellNumber]?.id || '',
                    role: robotPositions[cellNumber]?.leader ? 'leader' : 'follower',
                    status: robotPositions[cellNumber]?.missed > 0 ? 'inactive' : 'active',
                    task: robotPositions[cellNumber]?.task,
                    missed: robotPositions[cellNumber]?.missed
                  }} 
                />
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Loading dock (position 5) */}
      <div 
        style={loadingDockStyle}
        onClick={() => handleCellClick(5)}
      >
        <span style={cellNumberStyle}>5</span>
        {robotPositions[5] && (
          <div style={{ position: 'absolute' }}>
            <RobotNode 
              node={{
                id: robotPositions[5]?.id || '',
                role: robotPositions[5]?.leader ? 'leader' : robotPositions[5]?.leader == null ? 'ui' : 'follower',
                status: robotPositions[5]?.missed > 0 ? 'inactive' : 'active',
                task: robotPositions[5]?.task,
                missed: robotPositions[5]?.missed
              }} 
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackBox;
