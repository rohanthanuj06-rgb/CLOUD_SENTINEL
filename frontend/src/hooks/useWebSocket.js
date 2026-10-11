import { useState, useEffect, useRef, useCallback } from 'react';

export function useWebSocket(onMessageCallback) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessageTime, setLastMessageTime] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = import.meta.env.VITE_WS_URL || `${wsProtocol}//${window.location.hostname}:8000/ws`;

    try {
      const socket = new WebSocket(wsHost);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        // Start ping heartbeat
        if (socket.pingInterval) clearInterval(socket.pingInterval);
        socket.pingInterval = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'PING' }));
          }
        }, 15000);
      };

      socket.onmessage = (event) => {
        setLastMessageTime(new Date());
        try {
          const parsed = JSON.parse(event.data);
          if (onMessageCallback) {
            onMessageCallback(parsed);
          }
        } catch (e) {
          // ignore parsing error
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        if (socket.pingInterval) clearInterval(socket.pingInterval);
        // Attempt reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        socket.close();
      };
    } catch (err) {
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, [onMessageCallback]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        clearInterval(wsRef.current.pingInterval);
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return { isConnected, lastMessageTime };
}
