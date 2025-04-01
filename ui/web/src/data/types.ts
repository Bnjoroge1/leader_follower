export interface Node {
  id: string;
  role: 'leader' | 'follower';
  status: 'active' | 'inactive';
  task?: string;
  missed: number;
}