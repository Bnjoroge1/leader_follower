import React from 'react';

interface TrackBoxProps {
  className?: string;
  onCellClick?: (cellNumber: number) => void;
}

const TrackBox: React.FC<TrackBoxProps> = ({ className, onCellClick }) => {
  const containerStyle: React.CSSProperties = {
    padding: '20px',
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
  };

  const handleCellClick = (cellNumber: number) => {
    if (onCellClick) {
      onCellClick(cellNumber);
    }
  };

  return (
    <div className={`track-box ${className || ''}`} style={containerStyle}>
      <div style={gridStyle}>
        <div style={cellStyle} onClick={() => handleCellClick(1)}>1</div>
        <div style={cellStyle} onClick={() => handleCellClick(2)}>2</div>
        <div style={cellStyle} onClick={() => handleCellClick(3)}>3</div>
        <div style={cellStyle} onClick={() => handleCellClick(4)}>4</div>
      </div>
    </div>
  );
};

export default TrackBox;
