import { useEffect, useRef, useState } from "react";

import { apiRequest } from "../api/client";

export function useAntiCheat(sessionId) {
  const [warnings, setWarnings] = useState(0);
  const warnedRef = useRef(false);

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const sendEvent = async (eventType) => {
      try {
        await apiRequest("/contestants/monitoring-event", {
          method: "POST",
          body: JSON.stringify({ session_id: sessionId, event_type: eventType }),
        });
      } catch {
        // Keep exam flow running if telemetry post fails.
      }
    };

    const enforceFullscreen = async () => {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      }
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        setWarnings((value) => value + 1);
        sendEvent("TAB_SWITCH");
      }
    };

    const onFullscreenChange = () => {
      if (!document.fullscreenElement && warnedRef.current) {
        setWarnings((value) => value + 1);
        sendEvent("FULLSCREEN_EXIT");
      }
      warnedRef.current = true;
    };

    const blockContextMenu = (event) => {
      event.preventDefault();
    };

    const blockClipboardShortcuts = (event) => {
      if (event.ctrlKey && ["c", "v", "x", "u", "i"].includes(event.key.toLowerCase())) {
        event.preventDefault();
      }
    };

    enforceFullscreen();
    document.addEventListener("visibilitychange", onVisibilityChange);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    document.addEventListener("contextmenu", blockContextMenu);
    document.addEventListener("keydown", blockClipboardShortcuts);

    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      document.removeEventListener("fullscreenchange", onFullscreenChange);
      document.removeEventListener("contextmenu", blockContextMenu);
      document.removeEventListener("keydown", blockClipboardShortcuts);
    };
  }, [sessionId]);

  return { warnings };
}
