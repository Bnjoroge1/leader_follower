import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
// Assuming DeviceInfo structure based on errors and context
import { DeviceInfo } from '../../types/websocket'

interface GraphNode {
  id: string;
  val: number;
  color: string;
  device: DeviceInfo;
  x?: number;
  y?: number;
  fx?: number; // Fixed x position
  fy?: number; // Fixed y position
}

interface GraphLink {
  source: string;
  target: string;
  color: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface NetworkGraphProps {
  devices: DeviceInfo[];
  onDeviceSelect: (device: DeviceInfo | null) => void;
  width?: number;
  height?: number;
}

export function NetworkGraph({
  devices,
  onDeviceSelect,
  width = 800,
  height = 600
}: NetworkGraphProps) {
  const [highlightNodes, setHighlightNodes] = useState<Set<GraphNode>>(new Set())
  const [highlightLinks, setHighlightLinks] = useState<Set<GraphLink>>(new Set())
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  // Store fixed node positions across renders
  const nodePositionsRef = useRef<Map<string, { x: number, y: number }>>(new Map())

  // Track if initial layout is complete
  const [initialLayoutComplete, setInitialLayoutComplete] = useState(false)

  // Reference to the ForceGraph instance
  const graphRef = useRef<any>(null)

  const graphData = useMemo(() => {
    const data: GraphData = {
      nodes: [],
      links: []
    }
    const nodeMap = new Map<string, GraphNode>();

    // Create nodes 
    devices.forEach(device => {
      const nodeId = String(device.id);
      let nodeColor = '#3b82f6'; // Default blue (follower)

      if (device.active === false) {
        nodeColor = '#ef4444'; // Red for inactive devices
      } else if (device.leader) {
        nodeColor = '#22c55e'; // Green for active leader
      }

      // Get saved position for this node if it exists
      const savedPosition = nodePositionsRef.current.get(nodeId);

      const node: GraphNode = {
        id: nodeId,
        val: device.leader ? 20 : 10,
        color: nodeColor,
        device: device,
        // Apply fixed positions if we have saved coordinates and initial layout is done
        ...(initialLayoutComplete && savedPosition && {
          // Both set position and fix position
          x: savedPosition.x,
          y: savedPosition.y,
          fx: savedPosition.x, // Fixed x - critical to prevent movement
          fy: savedPosition.y  // Fixed y - critical to prevent movement
        })
      };

      data.nodes.push(node);
      nodeMap.set(nodeId, node);
    });

    // Create links
    devices.forEach(device => {
      if (!device.leader && device.leader_id !== null && device.leader_id !== undefined) {
        const sourceId = String(device.id);
        const targetId = String(device.leader_id);

        if (nodeMap.has(targetId)) {
          data.links.push({
            source: sourceId,
            target: targetId,
            color: '#94a3b8'
          });
        }
      }
    });

    return data
  }, [devices, initialLayoutComplete])

  // Function to save current node positions
  const saveNodePositions = useCallback(() => {
    if (!graphRef.current) return;

    try {
      // Get the current graph data from the force graph
      const currentData = graphRef.current.graphData();
      if (currentData && currentData.nodes) {
        // Save positions for all nodes
        currentData.nodes.forEach((node: GraphNode) => {
          if (node.x !== undefined && node.y !== undefined) {
            nodePositionsRef.current.set(node.id, { x: node.x, y: node.y });
          }
        });

        // Once positions are saved, mark layout as complete if not already
        if (!initialLayoutComplete) {
          console.log("Initial layout complete - fixing node positions");
          setInitialLayoutComplete(true);
        }
      }
    } catch (error) {
      console.error("Error saving node positions:", error);
    }
  }, [initialLayoutComplete]);

  // Engine stop handler - fix positions when simulation stops
  const handleEngineStop = useCallback(() => {
    saveNodePositions();
  }, [saveNodePositions]);

  // Apply fixed positions after drag
  const handleNodeDragEnd = useCallback((node: GraphNode) => {
    if (node.x !== undefined && node.y !== undefined) {
      // Update the position in our ref
      nodePositionsRef.current.set(node.id, { x: node.x, y: node.y });

      // Fix the node's position directly
      node.fx = node.x;
      node.fy = node.y;
    }
  }, []);

  const handleNodeClick = useCallback((node: GraphNode | null) => {
    setSelectedNode(node);
    onDeviceSelect(node ? node.device : null);
  }, [onDeviceSelect]);

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    const newHighlightNodes = new Set<GraphNode>();
    const newHighlightLinks = new Set<GraphLink>();

    if (node) {
      newHighlightNodes.add(node);
      graphData.links.forEach(link => {
        if (link.source === node.id || link.target === node.id) {
          newHighlightLinks.add(link);
        }
      });
    }
    setHighlightNodes(newHighlightNodes);
    setHighlightLinks(newHighlightLinks);

  }, [graphData.links]);

  return (
    <div className="border rounded-lg bg-white shadow-sm overflow-hidden">
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        nodeRelSize={6}
        width={width}
        height={height}
        backgroundColor="#ffffff"
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        nodeCanvasObject={(node: GraphNode, ctx, globalScale) => {
          const label = `Device ${node.id}`
          const fontSize = Math.max(1, (node.val / 2) / globalScale * 3);
          ctx.font = `${fontSize}px Inter`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';

          // Draw circle
          ctx.fillStyle = node.color;
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, node.val / 2, 0, 2 * Math.PI, false);
          ctx.fill();

          // Highlight border if node is highlighted or selected
          if (highlightNodes.has(node) || selectedNode === node) {
            ctx.strokeStyle = highlightNodes.has(node) ? '#f59e0b' : '#dc2626';
            ctx.lineWidth = 2 / globalScale;
            ctx.stroke();
          }

          // Draw label below the node
          ctx.fillStyle = '#334155';
          ctx.fillText(label, node.x!, node.y! + (node.val / 2) + (fontSize / 2));
        }}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        onNodeDragEnd={handleNodeDragEnd}
        linkColor={(link: GraphLink) => highlightLinks.has(link) ? '#f59e0b' : link.color}
        linkWidth={(link: GraphLink) => highlightLinks.has(link) ? 2 : 1}

        // Engine configuration - critical for stability
        cooldownTicks={50} // Let simulation settle initially
        cooldownTime={3000} // Max time for initial layout
        onEngineStop={handleEngineStop} // Save positions on cooldown
        d3VelocityDecay={0.6} // Higher decay means faster stabilization

        // Force configuration to improve initial layout
        d3Force={(forceName, force) => {
          if (forceName === 'charge') {
            // Stronger repulsion for better spacing
            force.strength(-300);
          }
          if (forceName === 'link') {
            // Longer links for better separation
            force.distance(60);
          }
          if (forceName === 'center') {
            // Better centering
            force.strength(0.1);
          }
        }}

        // Don't warm up, let the simulation run once for positioning
        warmupTicks={0}
        enableNodeDrag={true}
        enableZoomPanInteraction={true}
      />
    </div>
  )
}