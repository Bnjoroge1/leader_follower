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

interface NeighborhoodCluster {
  id: number;
  centerX: number;
  centerY: number;
  radius: number;
  color: string;
  devices: DeviceInfo[];
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  neighborhoods: NeighborhoodCluster[];
}

interface NetworkGraphProps {
  devices: DeviceInfo[];
  onDeviceSelect: (device: DeviceInfo | null) => void;
  width?: number;
  height?: number;
  onResetLayout?: () => void;
}

export function NetworkGraph({
  devices,
  onDeviceSelect,
  width = 800,
  height = 600,
  onResetLayout
}: NetworkGraphProps) {
  const [highlightNodes, setHighlightNodes] = useState<Set<GraphNode>>(new Set())
  const [highlightLinks, setHighlightLinks] = useState<Set<GraphLink>>(new Set())
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  // Store fixed node positions across renders
  const nodePositionsRef = useRef<Map<string, { x: number, y: number }>>(new Map())

  // Track if initial layout is complete
  const [initialLayoutComplete, setInitialLayoutComplete] = useState(false)

  // Reset layout when devices change significantly
  const resetLayout = useCallback(() => {
    nodePositionsRef.current.clear();
    setInitialLayoutComplete(false);
    console.log("Layout reset - will recalculate hierarchical positions");
    if (onResetLayout) {
      onResetLayout();
    }
  }, [onResetLayout])

  // Reference to the ForceGraph instance
  const graphRef = useRef<any>(null)

  // Generate distinct colors for neighborhoods
  const getNeighborhoodColor = useCallback((neighborhoodId: number) => {
    const colors = [
      '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57',
      '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
      '#10ac84', '#ee5a24', '#0984e3', '#6c5ce7', '#a29bfe',
      '#fd79a8', '#fdcb6e', '#e17055', '#81ecec', '#74b9ff'
    ];
    return colors[neighborhoodId % colors.length];
  }, [])

  // Track device count and hierarchy state to reset layout when needed
  const prevDeviceCountRef = useRef(devices.length)
  const prevHierarchyRef = useRef('')

  useEffect(() => {
    const currentDeviceCount = devices.length
    const currentHierarchy = devices.map(d => `${d.id}:${d.neighborhood_id}:${d.role}`).sort().join('|')

    // Reset layout if device count changes significantly or hierarchy changes
    if (Math.abs(currentDeviceCount - prevDeviceCountRef.current) > 2 ||
      currentHierarchy !== prevHierarchyRef.current) {
      console.log(`Hierarchy changed - resetting layout. Devices: ${prevDeviceCountRef.current} -> ${currentDeviceCount}`)
      resetLayout()
    }

    prevDeviceCountRef.current = currentDeviceCount
    prevHierarchyRef.current = currentHierarchy
  }, [devices, resetLayout])

  // Calculate initial hierarchical positioning for nodes
  const calculateHierarchicalPosition = useCallback((device: DeviceInfo, neighborhoods: Map<number, DeviceInfo[]>) => {
    const centerX = width / 2;
    const centerY = height / 2;
    const maxRadius = Math.min(width, height) / 2 - 50; // Smaller margin to use more space
    const councilRadius = maxRadius * 0.7; // Push council much further out (70% of max radius)
    const neighborhoodRadius = maxRadius * 0.4; // Larger radius for neighborhood devices

    // Position super leader at center
    if (device.is_super_leader) {
      return { x: centerX, y: centerY };
    }

    // Position neighborhood leaders in a circle around center (council)
    if (device.is_neighborhood_leader) {
      const neighborhoodCount = Math.max(1, neighborhoods.size);

      // For many neighborhoods, use a more spread out approach
      if (neighborhoodCount > 8) {
        // Use a grid-like pattern for many neighborhoods
        const cols = Math.ceil(Math.sqrt(neighborhoodCount));
        const rows = Math.ceil(neighborhoodCount / cols);
        const col = device.neighborhood_id % cols;
        const row = Math.floor(device.neighborhood_id / cols);

        const spacingX = (width * 0.8) / Math.max(1, cols - 1);
        const spacingY = (height * 0.8) / Math.max(1, rows - 1);

        return {
          x: width * 0.1 + col * spacingX,
          y: height * 0.1 + row * spacingY
        };
      } else {
        // Use circular layout for fewer neighborhoods
        const angle = (device.neighborhood_id * 2 * Math.PI) / neighborhoodCount;
        return {
          x: centerX + councilRadius * Math.cos(angle),
          y: centerY + councilRadius * Math.sin(angle)
        };
      }
    }

    // Position regular devices around their neighborhood leader
    const neighborhoodDevices = neighborhoods.get(device.neighborhood_id) || [];
    const deviceIndex = neighborhoodDevices.findIndex(d => d.id === device.id);
    const devicesInNeighborhood = Math.max(1, neighborhoodDevices.length);

    // Calculate neighborhood leader position using the same logic as above
    const neighborhoodCount = Math.max(1, neighborhoods.size);
    let leaderX, leaderY;

    if (neighborhoodCount > 8) {
      // Grid layout
      const cols = Math.ceil(Math.sqrt(neighborhoodCount));
      const rows = Math.ceil(neighborhoodCount / cols);
      const col = device.neighborhood_id % cols;
      const row = Math.floor(device.neighborhood_id / cols);
      const spacingX = (width * 0.8) / Math.max(1, cols - 1);
      const spacingY = (height * 0.8) / Math.max(1, rows - 1);
      leaderX = width * 0.1 + col * spacingX;
      leaderY = height * 0.1 + row * spacingY;
    } else {
      // Circular layout
      const neighborhoodAngle = (device.neighborhood_id * 2 * Math.PI) / neighborhoodCount;
      leaderX = centerX + councilRadius * Math.cos(neighborhoodAngle);
      leaderY = centerY + councilRadius * Math.sin(neighborhoodAngle);
    }

    // Position devices in a circle around their neighborhood leader
    // Skip the leader device itself in the circle
    const nonLeaderDevices = neighborhoodDevices.filter(d => !d.is_neighborhood_leader);
    const nonLeaderIndex = nonLeaderDevices.findIndex(d => d.id === device.id);

    if (nonLeaderIndex >= 0) {
      const deviceAngle = (nonLeaderIndex * 2 * Math.PI) / Math.max(1, nonLeaderDevices.length);
      const deviceRadius = neighborhoodRadius; // Distance from neighborhood leader

      return {
        x: leaderX + deviceRadius * Math.cos(deviceAngle),
        y: leaderY + deviceRadius * Math.sin(deviceAngle)
      };
    }

    // Fallback position (shouldn't reach here)
    return {
      x: leaderX + Math.random() * 100 - 50,
      y: leaderY + Math.random() * 100 - 50
    };
  }, [width, height])

  const graphData = useMemo(() => {
    const data: GraphData = {
      nodes: [],
      links: [],
      neighborhoods: []
    }
    const nodeMap = new Map<string, GraphNode>();

    // Group devices by neighborhoods for hierarchical layout
    const neighborhoods = new Map<number, DeviceInfo[]>();
    const councilMembers = new Set<number>();

    devices.forEach(device => {
      if (!neighborhoods.has(device.neighborhood_id)) {
        neighborhoods.set(device.neighborhood_id, []);
      }
      neighborhoods.get(device.neighborhood_id)!.push(device);

      if (device.is_neighborhood_leader) {
        councilMembers.add(device.id);
      }
    });

    // Debug: Log neighborhood distribution
    if (neighborhoods.size > 1) {
      console.log('Neighborhoods:', Array.from(neighborhoods.entries()).map(([id, devices]) =>
        `N${id}: ${devices.length} devices`));
    }

    // Create nodes with hierarchical positioning
    devices.forEach(device => {
      const nodeId = String(device.id);
      let nodeColor = getNeighborhoodColor(device.neighborhood_id);
      let nodeSize = 10;

      // Color and size based on hierarchy role, but keep neighborhood color base
      if (!device.active) {
        nodeColor = '#ef4444'; // Red for inactive devices
      } else if (device.is_super_leader) {
        nodeColor = '#1a1a1a'; // Black for super leader (stands out)
        nodeSize = 25;
      } else if (device.is_neighborhood_leader) {
        // Darker version of neighborhood color for leaders
        const baseColor = getNeighborhoodColor(device.neighborhood_id);
        nodeColor = baseColor; // Keep neighborhood color but make it prominent
        nodeSize = 20;
      } else {
        // Regular devices get a lighter version of neighborhood color
        nodeColor = getNeighborhoodColor(device.neighborhood_id);
        nodeSize = 12;
      }

      // Get saved position for this node if it exists
      const savedPosition = nodePositionsRef.current.get(nodeId);

      // Calculate hierarchical positioning
      let initialPosition = {};
      if (!initialLayoutComplete && !savedPosition) {
        initialPosition = calculateHierarchicalPosition(device, neighborhoods);
      }

      const node: GraphNode = {
        id: nodeId,
        val: nodeSize,
        color: nodeColor,
        device: device,
        // Apply fixed positions if we have saved coordinates and initial layout is done
        ...(initialLayoutComplete && savedPosition && {
          x: savedPosition.x,
          y: savedPosition.y,
          fx: savedPosition.x, // Fixed x - critical to prevent movement
          fy: savedPosition.y  // Fixed y - critical to prevent movement
        }),
        // Apply initial hierarchical positioning for new layout
        ...(!initialLayoutComplete && !savedPosition && initialPosition),
        // Always set fixed positions for hierarchical layout to prevent drift
        ...(initialPosition && !savedPosition && {
          fx: initialPosition.x,
          fy: initialPosition.y
        })
      };

      data.nodes.push(node);
      nodeMap.set(nodeId, node);
    });

    // Create hierarchical links
    devices.forEach(device => {
      // Links within neighborhoods (to neighborhood leader)
      if (!device.is_neighborhood_leader && device.neighborhood_leader_id) {
        const sourceId = String(device.id);
        const targetId = String(device.neighborhood_leader_id);

        if (nodeMap.has(targetId)) {
          data.links.push({
            source: sourceId,
            target: targetId,
            color: '#94a3b8' // Gray for neighborhood links
          });
        }
      }

      // Council links (neighborhood leaders to super leader)
      if (device.is_neighborhood_leader && !device.is_super_leader && device.super_leader_id) {
        const sourceId = String(device.id);
        const targetId = String(device.super_leader_id);

        if (nodeMap.has(targetId)) {
          data.links.push({
            source: sourceId,
            target: targetId,
            color: '#dc2626' // Red for council links
          });
        }
      }
    });

    // Create neighborhood clusters for background rendering
    neighborhoods.forEach((neighborhoodDevices, neighborhoodId) => {
      if (neighborhoodDevices.length === 0) return;

      // Calculate cluster center and radius based on node positions
      let centerX = 0, centerY = 0;
      let validPositions = 0;

      neighborhoodDevices.forEach(device => {
        const node = nodeMap.get(String(device.id));
        if (node && node.x !== undefined && node.y !== undefined) {
          centerX += node.x;
          centerY += node.y;
          validPositions++;
        } else {
          // Use calculated position if node position not yet set
          const position = calculateHierarchicalPosition(device, neighborhoods);
          centerX += position.x || 0;
          centerY += position.y || 0;
          validPositions++;
        }
      });

      if (validPositions > 0) {
        centerX /= validPositions;
        centerY /= validPositions;

        // Calculate radius to encompass all devices in neighborhood
        let maxDistance = 0;
        neighborhoodDevices.forEach(device => {
          const node = nodeMap.get(String(device.id));
          let deviceX, deviceY;

          if (node && node.x !== undefined && node.y !== undefined) {
            deviceX = node.x;
            deviceY = node.y;
          } else {
            const position = calculateHierarchicalPosition(device, neighborhoods);
            deviceX = position.x || centerX;
            deviceY = position.y || centerY;
          }

          const distance = Math.sqrt((deviceX - centerX) ** 2 + (deviceY - centerY) ** 2);
          maxDistance = Math.max(maxDistance, distance);
        });

        data.neighborhoods.push({
          id: neighborhoodId,
          centerX,
          centerY,
          radius: Math.max(maxDistance + 60, 120), // Much larger minimum radius of 120
          color: getNeighborhoodColor(neighborhoodId),
          devices: neighborhoodDevices
        });
      }
    });

    return data
  }, [devices, initialLayoutComplete, calculateHierarchicalPosition, getNeighborhoodColor])

  // Function to save current node positions
  const saveNodePositions = useCallback(() => {
    if (!graphRef.current) return;

    try {
      // Get the current graph data from the force graph
      if (typeof graphRef.current.graphData === 'function') {
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
    <div className="border rounded-lg bg-white shadow-sm overflow-hidden relative">
      {/* Reset Layout Button */}
      <button
        onClick={resetLayout}
        className="absolute top-2 right-2 z-10 px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded shadow-md transition-colors"
        title="Reset hierarchical layout"
      >
        Reset Layout
      </button>

      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        nodeRelSize={6}
        width={width}
        height={height}
        backgroundColor="#ffffff"

        // Custom background rendering for neighborhood clusters
        onRenderFramePre={(ctx, globalScale) => {
          // Draw neighborhood cluster backgrounds
          graphData.neighborhoods.forEach(neighborhood => {
            ctx.save();

            // Set up cluster background
            ctx.globalAlpha = 0.15; // Semi-transparent
            ctx.fillStyle = neighborhood.color;

            // Draw cluster circle
            ctx.beginPath();
            ctx.arc(neighborhood.centerX, neighborhood.centerY, neighborhood.radius, 0, 2 * Math.PI);
            ctx.fill();

            // Draw cluster border
            ctx.globalAlpha = 0.4;
            ctx.strokeStyle = neighborhood.color;
            ctx.lineWidth = 2 / globalScale;
            ctx.stroke();

            // Draw neighborhood label
            ctx.globalAlpha = 0.8;
            ctx.fillStyle = neighborhood.color;
            ctx.font = `${Math.max(12, 16 / globalScale)}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(
              `Neighborhood ${neighborhood.id}`,
              neighborhood.centerX,
              neighborhood.centerY - neighborhood.radius + 20
            );

            ctx.restore();
          });
        }}

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

        // Force configuration for hierarchical clustering
        d3Force={(forceName, force) => {
          if (forceName === 'charge') {
            // Stronger repulsion to spread neighborhoods apart
            force.strength(-200);
          }
          if (forceName === 'link') {
            // Longer links to separate neighborhoods more
            force.distance(80).strength(0.6);
          }
          if (forceName === 'center') {
            // Very weak centering to not interfere with fixed positions
            force.strength(0.02);
          }
          // Add custom clustering force
          if (forceName === 'x') {
            // Disable x positioning force since we use fixed positions
            force.strength(0);
          }
          if (forceName === 'y') {
            // Disable y positioning force since we use fixed positions  
            force.strength(0);
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