import { useEffect, useRef, useState } from "react";

import { apiRequest } from "../api/client";

const MAX_WARNINGS_BEFORE_AUTOSUBMIT = 2;

export function useAntiCheat(sessionId, onAutoSubmit) {
  const [warnings, setWarnings] = useState(0);
  const [lastEvent, setLastEvent] = useState("");
  const warnedRef = useRef(false);
  const warningCountRef = useRef(0);

  useEffect(() => {
    warnedRef.current = false;
    warningCountRef.current = 0;
    setWarnings(0);
    setLastEvent("");
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

    const sendEvent = async (eventType, eventMeta = {}) => {
      try {
        await apiRequest("/contestants/monitoring-event", {
          method: "POST",
          body: JSON.stringify({
            session_id: sessionId,
            event_type: eventType,
            event_meta: {
              timestamp: new Date().toISOString(),
              warning_count: warningCountRef.current,
              ...eventMeta,
            },
          }),
        });
      } catch {
        // Keep exam flow running if telemetry post fails.
      }
    };

    const registerViolation = async (eventType) => {
      warningCountRef.current += 1;
      setWarnings(warningCountRef.current);
      setLastEvent(eventType);
      await sendEvent(eventType, { warning_count: warningCountRef.current });

      if (warningCountRef.current >= MAX_WARNINGS_BEFORE_AUTOSUBMIT) {
        await sendEvent("AUTO_SUBMIT_TRIGGER", {
          reason: "MAX_VIOLATIONS",
        });
        if (onAutoSubmit) {
          onAutoSubmit("MAX_VIOLATIONS");
        }
      }
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        void registerViolation("TAB_SWITCH");
      }
    };

    const onFullscreenChange = async () => {
      if (!document.fullscreenElement && warnedRef.current) {
        try {
          await sendEvent("FULLSCREEN_EXIT");
        } catch (error) {
          console.warn("Failed to send FULLSCREEN_EXIT telemetry.", error);
        }

        if (onAutoSubmit) {
          onAutoSubmit("FULLSCREEN_EXIT");
        }
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
        void sendEvent("SHORTCUT_BLOCKED", {
          key: event.key.toLowerCase(),
        });
      }

      if (event.key === "F12") {
        event.preventDefault();
        void sendEvent("DEVTOOLS_SHORTCUT_BLOCKED", { key: "F12" });
      }

      if (
        shortcutPressed
        && event.shiftKey
        && ["i", "j", "c"].includes(event.key.toLowerCase())
      ) {
        event.preventDefault();
        void sendEvent("DEVTOOLS_SHORTCUT_BLOCKED", {
          key: `${event.ctrlKey ? "ctrl" : "meta"}+shift+${event.key.toLowerCase()}`,
        });
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
  }, [sessionId, onAutoSubmit]);

  return {
    warnings,
    lastEvent,
    requestFullscreenFromGesture,
  };
}
