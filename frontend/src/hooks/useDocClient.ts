"use client";

import { useState, useEffect, useRef } from "react";

type UDocClientInstance = Awaited<
  ReturnType<(typeof import("@docmentis/udoc-viewer"))["UDocClient"]["create"]>
>;

export function useDocClient() {
  const [client, setClient] = useState<UDocClientInstance | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const destroyingRef = useRef(false);

  useEffect(() => {
    let instance: UDocClientInstance | null = null;
    destroyingRef.current = false;

    (async () => {
      try {
        const { UDocClient } = await import("@docmentis/udoc-viewer");
        instance = await UDocClient.create();
        if (!destroyingRef.current) {
          setClient(instance);
          setIsReady(true);
        } else {
          instance.destroy();
        }
      } catch (err) {
        if (!destroyingRef.current) {
          setError(
            err instanceof Error ? err.message : "Failed to load document viewer",
          );
        }
      }
    })();

    return () => {
      destroyingRef.current = true;
      if (instance) {
        instance.destroy();
      }
    };
  }, []);

  return { client, isReady, error };
}
