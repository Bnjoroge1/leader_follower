
import React, { useState, useMemo } from 'react';
import { useStore } from '@nanostores/react';
import { deviceList } from '../../stores/websocket'; // Adjust import path
import { Button } from './button'; // Assuming you have a Button component
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel } from './select'; // Assuming shadcn/ui select
import { Input } from './input'; // For search functionality
import { Search, Crown, Shield, Users } from 'lucide-react';

// Define the base URL for your simulation API
const API_BASE_URL = 'http://localhost:8080/simulate';

async function sendSimulationCommand(command: string, deviceId: string | number) {
  if (!deviceId) {
    alert('Please select a device ID.');
    return;
  }
  const url = `${API_BASE_URL}/${command}/${deviceId}`;
  console.log(`Sending command: POST ${url}`);
  try {
    const response = await fetch(url, { method: 'POST' });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(`API Error (${response.status}): ${text}`);
    }
    console.log(`Command ${command} for ${deviceId} successful: ${text}`);
    alert(`Command ${command} for ${deviceId} sent: ${text}`);
  } catch (error) {
    console.error(`Failed to send command ${command} for ${deviceId}:`, error);
    alert(`Failed to send command ${command} for ${deviceId}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

export function SimulationControls() {
  const devices = useStore(deviceList);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const handleDeviceChange = (value: string) => {
    setSelectedDeviceId(value);
  };

  // Function to get role display info
  const getRoleInfo = (device: any) => {
    if (device.is_super_leader) {
      return { label: 'Super Leader', icon: Crown, color: 'text-yellow-600' };
    } else if (device.is_neighborhood_leader) {
      return { label: 'Leader', icon: Shield, color: 'text-blue-600' };
    } else if (device.leader) {
      return { label: 'Leader', icon: Shield, color: 'text-blue-600' };
    }
    return { label: '', icon: Users, color: 'text-gray-500' };
  };

  // Filter and sort devices based on search term and role
  const filteredAndSortedDevices = useMemo(() => {
    let filtered = devices;

    // Filter by search term
    if (searchTerm) {
      filtered = devices.filter(device =>
        device.id.toString().includes(searchTerm) ||
        getRoleInfo(device).label.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort by role priority, then by ID
    return filtered.sort((a, b) => {
      // Super leaders first
      if (a.is_super_leader && !b.is_super_leader) return -1;
      if (!a.is_super_leader && b.is_super_leader) return 1;

      // Then neighborhood leaders
      if (a.is_neighborhood_leader && !b.is_neighborhood_leader) return -1;
      if (!a.is_neighborhood_leader && b.is_neighborhood_leader) return 1;

      // Then regular leaders
      if (a.leader && !b.leader) return -1;
      if (!a.leader && b.leader) return 1;

      // Finally by ID
      return a.id - b.id;
    });
  }, [devices, searchTerm]);

  // Group devices by role for better organization
  const groupedDevices = useMemo(() => {
    const groups = {
      superLeaders: filteredAndSortedDevices.filter(d => d.is_super_leader),
      neighborhoodLeaders: filteredAndSortedDevices.filter(d => d.is_neighborhood_leader && !d.is_super_leader),
      regularLeaders: filteredAndSortedDevices.filter(d => d.leader && !d.is_neighborhood_leader && !d.is_super_leader),
      devices: filteredAndSortedDevices.filter(d => !d.leader && !d.is_neighborhood_leader && !d.is_super_leader)
    };
    return groups;
  }, [filteredAndSortedDevices]);

  // Helper function to render device item
  const renderDeviceItem = (device: any) => {
    const roleInfo = getRoleInfo(device);
    const Icon = roleInfo.icon;
    return (
      <SelectItem key={device.id} value={String(device.id)}>
        <div className="flex items-center gap-2 w-full">
          <Icon className={`h-4 w-4 ${roleInfo.color}`} />
          <span>Device {device.id}</span>
          {roleInfo.label && (
            <span className={`text-xs px-2 py-1 rounded-full bg-gray-100 ${roleInfo.color} font-medium`}>
              {roleInfo.label}
            </span>
          )}
          <span className="text-xs text-gray-500 ml-auto">
            N{device.neighborhood_id}
          </span>
        </div>
      </SelectItem>
    );
  };

  return (
    <div className="mt-6 p-4 border rounded-lg shadow bg-card">
      <h2 className="text-xl font-semibold mb-4">Simulation Controls</h2>

      {/* Search Input */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search by device ID or role..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 w-full max-w-sm"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-4 items-center">
        <Select value={selectedDeviceId} onValueChange={handleDeviceChange}>
          <SelectTrigger className="w-[280px]">
            <SelectValue placeholder="Select Device ID" />
          </SelectTrigger>
          <SelectContent className="max-h-[300px]">
            {groupedDevices.superLeaders.length > 0 && (
              <SelectGroup>
                <SelectLabel className="flex items-center gap-2">
                  <Crown className="h-4 w-4 text-yellow-600" />
                  Super Leaders
                </SelectLabel>
                {groupedDevices.superLeaders.map(renderDeviceItem)}
              </SelectGroup>
            )}

            {groupedDevices.neighborhoodLeaders.length > 0 && (
              <SelectGroup>
                <SelectLabel className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-600" />
                  Neighborhood Leaders
                </SelectLabel>
                {groupedDevices.neighborhoodLeaders.map(renderDeviceItem)}
              </SelectGroup>
            )}

            {groupedDevices.regularLeaders.length > 0 && (
              <SelectGroup>
                <SelectLabel className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-600" />
                  Leaders
                </SelectLabel>
                {groupedDevices.regularLeaders.map(renderDeviceItem)}
              </SelectGroup>
            )}

            {groupedDevices.devices.length > 0 && (
              <SelectGroup>
                <SelectLabel className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-gray-500" />
                  Devices
                </SelectLabel>
                {groupedDevices.devices.map(renderDeviceItem)}
              </SelectGroup>
            )}

            {filteredAndSortedDevices.length === 0 && (
              <div className="p-4 text-center text-gray-500">
                No devices found matching "{searchTerm}"
              </div>
            )}
          </SelectContent>
        </Select>

        <Button variant="destructive" size="sm" onClick={() => sendSimulationCommand('stop', selectedDeviceId)} disabled={!selectedDeviceId}>
          Stop Process
        </Button>
        {/* <Button variant="secondary" size="sm" onClick={() => sendSimulationCommand('start', selectedDeviceId)} disabled={!selectedDeviceId}>
          Start Process
        </Button> */}
        <Button variant="outline" size="sm" onClick={() => sendSimulationCommand('deactivate', selectedDeviceId)} disabled={!selectedDeviceId}>
          Deactivate
        </Button>
        <Button variant="outline" size="sm" onClick={() => sendSimulationCommand('activate', selectedDeviceId)} disabled={!selectedDeviceId}>
          Activate
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        Note: 'Stop Process' terminates the device's simulation process. 'Deactivate'/'Activate' toggle the internal active flag. Use search to quickly find devices by ID or role.
      </p>
      {selectedDeviceId && (
        <p className="text-xs text-blue-600 mt-1">
          Selected: Device {selectedDeviceId} {(() => {
            const device = devices.find(d => d.id.toString() === selectedDeviceId);
            if (!device) return '';
            const roleInfo = getRoleInfo(device);
            return roleInfo.label ? `(${roleInfo.label})` : '';
          })()}
        </p>
      )}
    </div>
  );
}