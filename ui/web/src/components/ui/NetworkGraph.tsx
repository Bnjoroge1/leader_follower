import { useCallback, useMemo, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
// Assuming DeviceInfo structure based on errors and context
import { DeviceInfo } from '../../types/websocket' // { id: number; is_leader: boolean; leader_id: number | null; ... }

interface GraphNode {
  id: string; // Force graph needs string IDs
  val: number; // size
  color: string;
  device: DeviceInfo; // Keep original device info
  x?: number; // ForceGraph adds these
  y?: number; // ForceGraph adds these
}

interface GraphLink {
    source: string; // Force graph needs string IDs
    target: string; // Force graph needs string IDs
    color: string;
}


interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface NetworkGraphProps {
  devices: DeviceInfo[];
  // Prop name changed in App.tsx, ensure it matches here
  onDeviceSelect: (device: DeviceInfo | null) => void;
  width?: number;
  height?: number;
}

export function NetworkGraph({
  devices,
  onDeviceSelect,
  width = 800, // Default width
  height = 600 // Default height
}: NetworkGraphProps) {
  const [highlightNodes, setHighlightNodes] = useState<Set<GraphNode>>(new Set())
  const [highlightLinks, setHighlightLinks] = useState<Set<GraphLink>>(new Set())
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  const graphData = useMemo(() => {
    const data: GraphData = {
      nodes: [],
      links: []
    }
    const nodeMap = new Map<string, GraphNode>(); // Helper to find nodes by ID quickly

    // Create nodes
    devices.forEach(device => {
      const nodeId = String(device.id); // Use string ID for graph
      const node: GraphNode = {
        id: nodeId,
        // Use is_leader for size/color
        val: device.leader ? 20 : 10, // Leaders are bigger
        color: device.leader ? '#22c55e' : '#3b82f6', // green for leaders, blue for followers
        device: device // Store original device object
      };
      data.nodes.push(node);
      nodeMap.set(nodeId, node);
    });

    // Create links (follower to leader)
    devices.forEach(device => {
      // Ensure it's a follower and has a leader_id assigned
      if (!device.leader && device.leaderr !== null && device.leader_id !== undefined) {
         const sourceId = String(device.id);
         const targetId = String(device.leader); // Use leader_id as target

         // Ensure the target leader node exists in the current list
         if (nodeMap.has(targetId)) {
            data.links.push({
              source: sourceId,
              target: targetId,
              color: '#94a3b8' // slate-400
            });
         } else {
            console.warn(`Leader node ${targetId} not found for follower ${sourceId}`);
         }
      }
    });


    return data
  }, [devices])

  const handleNodeClick = useCallback((node: GraphNode | null) => {
    setSelectedNode(node);
    // Pass the original DeviceInfo object back
    onDeviceSelect(node ? node.device : null);
  }, [onDeviceSelect]);


  // Type the node parameter explicitly
  const handleNodeHover = useCallback((node: GraphNode | null) => {
    const newHighlightNodes = new Set<GraphNode>();
    const newHighlightLinks = new Set<GraphLink>();

    if (node) {
        newHighlightNodes.add(node);
        // Add incoming and outgoing links
        graphData.links.forEach(link => {
            if (link.source === node.id || link.target === node.id) {
                newHighlightLinks.add(link);
            }
        });
    }
    setHighlightNodes(newHighlightNodes);
    setHighlightLinks(newHighlightLinks);

  }, [graphData.links]); // Dependency on graphData.links

  return (
    <div className="border rounded-lg bg-white shadow-sm overflow-hidden"> {/* Added overflow-hidden */}
      <ForceGraph2D
        graphData={graphData}
        nodeRelSize={6}
        width={width}
        height={height}
        backgroundColor="#ffffff"
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        // Type node parameter explicitly
        nodeCanvasObject={(node: GraphNode, ctx, globalScale) => {
          const label = `Device ${node.id}`
          // Adjust font size based on node value and scale
          const fontSize = Math.max(1, (node.val / 2) / globalScale * 3); // Adjust multiplier as needed
          ctx.font = `${fontSize}px Inter`; // Use a common font stack
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';

          // Draw circle
          ctx.fillStyle = node.color; // Use node's assigned color
          ctx.beginPath();
          // Use node.x and node.y provided by the engine
          ctx.arc(node.x!, node.y!, node.val / 2, 0, 2 * Math.PI, false);
          ctx.fill();

           // Highlight border if node is highlighted or selected
           if (highlightNodes.has(node) || selectedNode === node) {
             ctx.strokeStyle = highlightNodes.has(node) ? '#f59e0b' : '#dc2626'; // Amber for hover, Red for selected
             ctx.lineWidth = 2 / globalScale; // Make border consistent size
             ctx.stroke();
           }


          // Draw label below the node
          ctx.fillStyle = '#334155'; // Darker text (slate-700)
          // Position label below the circle
          ctx.fillText(label, node.x!, node.y! + (node.val / 2) + (fontSize / 2));
        }}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        // Type link parameter explicitly
        linkColor={(link: GraphLink) => highlightLinks.has(link) ? '#f59e0b' : link.color} // Amber highlight
        linkWidth={(link: GraphLink) => highlightLinks.has(link) ? 2 : 1}
        // Disable node coloring here if handled in nodeCanvasObject
        // nodeColor={(node: GraphNode) => ... } // Remove or adjust if using nodeCanvasObject for color

        cooldownTicks={100} // Let simulation settle
        d3VelocityDecay={0.3} // Faster decay for less movement
        // Consider adding forces for better layout if needed
        // d3Force={'link', d3.forceLink(graphData.links).id((d: any) => d.id).distance(50)}
        // d3Force={'charge', d3.forceManyBody().strength(-100)}
        // d3Force={'center', d3.forceCenter()}
      />
    </div>
  )
}