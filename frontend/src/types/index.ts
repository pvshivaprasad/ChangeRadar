import { LucideIcon } from 'lucide-react';

export type PageId =
  | 'overview'
  | 'repositories'
  | 'analysis'
  | 'dependencies'
  | 'tests'
  | 'reports';

export interface NavItem {
  id: PageId;
  label: string;
  icon: LucideIcon;
  badge?: string;
}

export type Theme = 'light' | 'dark';

export interface DatabaseStatus {
  connected: boolean;
  dialect: string;
  error?: string | null;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'offline';
  service: string;
  version: string;
  environment: string;
  database: DatabaseStatus;
  responseTimeMs?: number;
}
