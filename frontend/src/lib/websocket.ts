'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useSimulationStore } from './store';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket(simulationId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const { setMacroState, addHistoryEntry, setIsRunning } = useSimulationStore();

  const connect = useCallback(() => {
    if (!simulationId) return;

    const ws = new WebSocket(`${WS_URL}/ws/simulation/${simulationId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      ws.send(JSON.stringify({ type: 'subscribe' }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);

      switch (data.type) {
        case 'subscribed':
          console.log('Subscribed to simulation updates');
          break;
        case 'state_update':
          setMacroState(data.macro_state);
          addHistoryEntry({
            tick: data.macro_state.tick,
            macro_state: data.macro_state,
            timestamp: new Date().toISOString(),
          });
          break;
        case 'simulation_started':
          setIsRunning(true);
          break;
        case 'simulation_paused':
        case 'simulation_stopped':
        case 'simulation_completed':
          setIsRunning(false);
          break;
        case 'pong':
          // Heartbeat response
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Attempt to reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };

    wsRef.current = ws;
  }, [simulationId, setMacroState, addHistoryEntry, setIsRunning]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    connect();
    
    // Heartbeat
    const heartbeat = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 30000);

    return () => {
      clearInterval(heartbeat);
      disconnect();
    };
  }, [connect, disconnect, sendMessage]);

  return { sendMessage, disconnect, reconnect: connect, isConnected, lastMessage };
}

// Hook for managing simulation polling (fallback for WebSocket)
export function useSimulationPolling(simulationId: string | null, interval = 1000) {
  const { setMacroState, addHistoryEntry, currentSimulation, setCurrentSimulation } = useSimulationStore();
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!simulationId || currentSimulation?.status !== 'running') {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    const poll = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/simulations/${simulationId}/state`
        );
        if (response.ok) {
          const data = await response.json();
          setMacroState(data);
          addHistoryEntry({
            tick: data.tick,
            macro_state: data,
            timestamp: new Date().toISOString(),
          });
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [simulationId, currentSimulation?.status, interval, setMacroState, addHistoryEntry, setCurrentSimulation]);
}
