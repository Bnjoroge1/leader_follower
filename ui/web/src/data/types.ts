export interface Node {
  id: string;
  role: 'leader' | 'follower' | 'ui';
  status: 'active' | 'inactive';
  task?: string;
  missed: number;
}