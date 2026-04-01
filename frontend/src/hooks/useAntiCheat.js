import { useEffect, useRef, useState } from "react";

import { apiRequest } from "../api/client";

export function useAntiCheat(sessionId) {
  const [warnings, setWarnings] = useState(0);
  const warnedRef = useRef(false);

  useEffect(() => {
    warnedRef.current = false;
  }, [sessionId]);

  const requestFullscreenFromGesture = async () => {
    if (document.fullscreenElement) {
      return true;
    }

    try {
      await document.documentElement.requestFullscreen();
      return true;
    } catch (error) {
      console.warn("Fullscreen request failed; continuing with telemetry only.", error);
      return false;
    }
  };

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
      const shortcutPressed = event.ctrlKey || event.metaKey;
      if (shortcutPressed && ["c", "v", "x", "u", "i"].includes(event.key.toLowerCase())) {
        event.preventDefault();
      }
    };

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

  return {
    warnings,
    requestFullscreenFromGesture,
  };
}
