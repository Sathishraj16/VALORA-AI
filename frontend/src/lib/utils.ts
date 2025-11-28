import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options,
  }).format(value);
}

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatCompact(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  return value.toFixed(2);
}

export function getChangeIndicator(value: number): {
  direction: 'up' | 'down' | 'neutral';
  color: string;
  icon: string;
} {
  if (value > 0.001) {
    return { direction: 'up', color: 'text-accent-400', icon: '↑' };
  }
  if (value < -0.001) {
    return { direction: 'down', color: 'text-red-400', icon: '↓' };
  }
  return { direction: 'neutral', color: 'text-dark-400', icon: '→' };
}

export function getCyclePhaseColor(phase: string): string {
  switch (phase?.toLowerCase()) {
    case 'expansion':
      return 'text-accent-400 bg-accent-600/20';
    case 'peak':
      return 'text-yellow-400 bg-yellow-600/20';
    case 'contraction':
      return 'text-red-400 bg-red-600/20';
    case 'trough':
      return 'text-orange-400 bg-orange-600/20';
    default:
      return 'text-dark-400 bg-dark-600/20';
  }
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'running':
      return 'text-accent-400 bg-accent-600/20 border-accent-600/30';
    case 'paused':
      return 'text-yellow-400 bg-yellow-600/20 border-yellow-600/30';
    case 'completed':
      return 'text-primary-400 bg-primary-600/20 border-primary-600/30';
    case 'failed':
      return 'text-red-400 bg-red-600/20 border-red-600/30';
    default:
      return 'text-dark-400 bg-dark-600/20 border-dark-600/30';
  }
}

export function getRiskColor(score: number): string {
  if (score >= 0.7) return 'text-red-400';
  if (score >= 0.4) return 'text-yellow-400';
  return 'text-accent-400';
}

export function truncateAddress(address: string, start = 6, end = 4): string {
  if (address.length <= start + end) return address;
  return `${address.slice(0, start)}...${address.slice(-end)}`;
}

export function timeAgo(date: Date | string): string {
  const now = new Date();
  const past = new Date(date);
  const diffMs = now.getTime() - past.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return past.toLocaleDateString();
}

export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

export function mapRange(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
): number {
  return ((value - inMin) * (outMax - outMin)) / (inMax - inMin) + outMin;
}
