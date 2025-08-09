import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { DeviceInfo } from '../../types/websocket'

interface CouncilNode {
     id: string;
     val: number;
     color: string;
     device: DeviceInfo;
     x?: number;
     y?: number;
     fx?: number;
     fy?: number;
}

interface CouncilLink {
     source: string;
     target: string;
     color: string;
}

interface CouncilData {
     nodes: CouncilNode[];
     links: CouncilLink[];
}

interface CouncilViewProps {
     devices: DeviceInfo[];
     onDeviceSelect: (device: DeviceInfo | null) => void;
     width?: number;
     height?: number;
}

export function CouncilView({
     devices,
     onDeviceSelect,
     width = 600,
     height = 400
}: CouncilViewProps) {
     const [highlightNodes, setHighlightNodes] = useState<Set<CouncilNode>>(new Set())
     const [highlightLinks, setHighlightLinks] = useState<Set<CouncilLink>>(new Set())
     const [selectedNode, setSelectedNode] = useState<CouncilNode | null>(null)

     const nodePositionsRef = useRef<Map<string, { x: number, y: number }>>(new Map())
     const [initialLayoutComplete, setInitialLayoutComplete] = useState(false)
     const graphRef = useRef<any>(null)

     // Filter to show only neighborhood leaders and super leader
     const councilMembers = useMemo(() => {
          return devices.filter(device => device.is_neighborhood_leader || device.is_super_leader);
     }, [devices]);

     const graphData = useMemo(() => {
          const data: CouncilData = {
               nodes: [],
               links: []
          }
          const nodeMap = new Map<string, CouncilNode>();

          // Create nodes for council members only
          councilMembers.forEach((device, index) => {
               const nodeId = String(device.id);
               let nodeColor = '#f59e0b'; // Amber for neighborhood leaders
               let nodeSize = 20;

               if (!device.active) {
                    nodeColor = '#ef4444'; // Red for inactive
               } else if (device.is_super_leader) {
                    nodeColor = '#9333ea'; // Purple for super leader
                    nodeSize = 30;
               }

               // Get saved position or calculate circular layout
               const savedPosition = nodePositionsRef.current.get(nodeId);
               let initialPosition = {};

               if (!initialLayoutComplete && !savedPosition) {
                    const centerX = width / 2;
                    const centerY = height / 2;
                    const radius = Math.min(width, height) / 4;

                    if (device.is_super_leader) {
                         // Super leader at center
                         initialPosition = { x: centerX, y: centerY };
                    } else {
                         // Other leaders in circle around super leader
                         const angle = (index * 2 * Math.PI) / councilMembers.length;
                         initialPosition = {
                              x: centerX + radius * Math.cos(angle),
                              y: centerY + radius * Math.sin(angle)
                         };
                    }
               }

               const node: CouncilNode = {
                    id: nodeId,
                    val: nodeSize,
                    color: nodeColor,
                    device: device,
                    ...(initialLayoutComplete && savedPosition && {
                         x: savedPosition.x,
                         y: savedPosition.y,
                         fx: savedPosition.x,
                         fy: savedPosition.y
                    }),
                    ...(!initialLayoutComplete && !savedPosition && initialPosition)
               };

               data.nodes.push(node);
               nodeMap.set(nodeId, node);
          });

          // Create links between neighborhood leaders and super leader
          councilMembers.forEach(device => {
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

          return data;
     }, [councilMembers, width, height, initialLayoutComplete]);

     const saveNodePositions = useCallback(() => {
          if (!graphRef.current) return;

          try {
               const currentData = graphRef.current.graphData();
               if (currentData && currentData.nodes) {
                    currentData.nodes.forEach((node: CouncilNode) => {
                         if (node.x !== undefined && node.y !== undefined) {
                              nodePositionsRef.current.set(node.id, { x: node.x, y: node.y });
                         }
                    });

                    if (!initialLayoutComplete) {
                         setInitialLayoutComplete(true);
                    }
               }
          } catch (error) {
               console.error("Error saving council node positions:", error);
          }
     }, [initialLayoutComplete]);

     const handleNodeClick = useCallback((node: CouncilNode) => {
          setSelectedNode(node);
          onDeviceSelect(node.device);
     }, [onDeviceSelect]);

     const handleNodeHover = useCallback((node: CouncilNode | null) => {
          if (!node) {
               setHighlightNodes(new Set());
               setHighlightLinks(new Set());
               return;
          }

          const highlightNodesSet = new Set<CouncilNode>();
          const highlightLinksSet = new Set<CouncilLink>();

          highlightNodesSet.add(node);

          // Highlight connected nodes and links
          graphData.links.forEach(link => {
               if (link.source === node.id || link.target === node.id) {
                    highlightLinksSet.add(link);

                    const connectedNodeId = link.source === node.id ? link.target : link.source;
                    const connectedNode = graphData.nodes.find(n => n.id === connectedNodeId);
                    if (connectedNode) {
                         highlightNodesSet.add(connectedNode);
                    }
               }
          });

          setHighlightNodes(highlightNodesSet);
          setHighlightLinks(highlightLinksSet);
     }, [graphData]);

     // Auto-save positions when simulation ends
     useEffect(() => {
          const timer = setTimeout(() => {
               if (graphRef.current && !initialLayoutComplete) {
                    saveNodePositions();
               }
          }, 3000); // Save after 3 seconds

          return () => clearTimeout(timer);
     }, [saveNodePositions, initialLayoutComplete]);

     if (councilMembers.length === 0) {
          return (
               <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
                    <div className="text-center">
                         <h3 className="text-lg font-medium text-gray-900 mb-2">No Council Members</h3>
                         <p className="text-sm text-gray-500">
                              Enable hierarchical mode to see the council of neighborhood leaders
                         </p>
                    </div>
               </div>
          );
     }

     return (
          <div className="bg-white rounded-lg shadow-sm border">
               <div className="p-4 border-b">
                    <h3 className="text-lg font-medium">Council of Leaders</h3>
                    <p className="text-sm text-gray-500 mt-1">
                         {councilMembers.length} neighborhood leaders
                    </p>
               </div>

               <div className="relative">
                    <ForceGraph2D
                         ref={graphRef}
                         graphData={graphData}
                         width={width}
                         height={height}
                         nodeLabel={(node: any) => {
                              const device = node.device as DeviceInfo;
                              return `
              <div style="background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 12px;">
                <div><strong>Device ${device.id}</strong></div>
                <div>Role: ${device.role}</div>
                <div>Neighborhood: ${device.neighborhood_id}</div>
                <div>Status: ${device.active ? 'Active' : 'Inactive'}</div>
              </div>
            `;
                         }}
                         nodeColor={(node: any) => {
                              const councilNode = node as CouncilNode;
                              return highlightNodes.has(councilNode) ? '#fbbf24' : councilNode.color;
                         }}
                         nodeVal={(node: any) => (node as CouncilNode).val}
                         linkColor={(link: any) => {
                              const councilLink = link as CouncilLink;
                              return highlightLinks.has(councilLink) ? '#fbbf24' : councilLink.color;
                         }}
                         linkWidth={(link: any) => highlightLinks.has(link as CouncilLink) ? 3 : 2}
                         onNodeClick={handleNodeClick}
                         onNodeHover={handleNodeHover}
                         onEngineStop={saveNodePositions}
                         cooldownTicks={100}
                         d3AlphaDecay={0.02}
                         d3VelocityDecay={0.3}
                    />
               </div>
          </div>
     );
}
