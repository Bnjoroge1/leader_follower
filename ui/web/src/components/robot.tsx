import React from 'react';
import { Node } from '../data/types';

interface RobotNodeProps {
  node: Node;
}

const RobotNode: React.FC<RobotNodeProps> = ({ node }) => {
  const nodeColor = node.role === 'leader' ? 'red' : 'blue';
  
  const circleStyle: React.CSSProperties = {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    backgroundColor: nodeColor,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    color: 'white',
    fontWeight: 'bold',
    opacity: node.status === 'active' ? 1 : 0.5,
  };
  
  return (
    <div style={circleStyle}>
      {node.id}
    </div>
  );
};

export default RobotNode;
