"use client";

// Loaded with next/dynamic({ ssr: false }) — Excalidraw needs the browser.
import { useCallback, useMemo, useRef } from "react";
import {
  CaptureUpdateAction,
  Excalidraw,
  ROUNDNESS,
  convertToExcalidrawElements,
  getSceneVersion,
  viewportCoordsToSceneCoords,
} from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import type {
  ExcalidrawImperativeAPI,
  ExcalidrawInitialDataState,
} from "@excalidraw/excalidraw/types";
import type { ExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import type { ExcalidrawElementSkeleton } from "@excalidraw/excalidraw/data/transform";
import {
  COMPONENT_PALETTE,
  arrowGeometry,
  layoutReferenceDesign,
  type PaletteItem,
  type ReferenceBrief,
} from "@/lib/system-design";

export interface DesignCanvasHandle {
  addComponent: (item: PaletteItem) => void;
  /** Select and scroll to these elements (e.g. an unconnected arrow). */
  focusElements: (ids: string[]) => void;
}

const BOX_WIDTH = 180;
const BOX_HEIGHT = 70;

function paletteSkeleton(
  item: PaletteItem,
  x: number,
  y: number,
  width = BOX_WIDTH,
  height = BOX_HEIGHT,
  text: string = item.label,
  id?: string,
): ExcalidrawElementSkeleton {
  return {
    type: item.shape,
    id,
    x,
    y,
    width,
    height,
    backgroundColor: item.color,
    fillStyle: "solid",
    roundness:
      item.shape === "rectangle" ? { type: ROUNDNESS.ADAPTIVE_RADIUS } : null,
    customData: { kind: item.kind },
    label: { text },
  };
}

function referenceElements(reference: ReferenceBrief) {
  const boxes = layoutReferenceDesign(
    reference.reference_components,
    reference.reference_connections,
  );
  const byId = new Map(reference.reference_components.map((c) => [c.id, c]));
  const boxById = new Map(boxes.map((b) => [b.id, b]));
  const fallback = COMPONENT_PALETTE.find((p) => p.kind === "service")!;
  const skeleton: ExcalidrawElementSkeleton[] = boxes.map((b) => {
    const comp = byId.get(b.id)!;
    const item =
      COMPONENT_PALETTE.find((p) => p.kind === comp.kind) ?? fallback;
    return paletteSkeleton(item, b.x, b.y, b.width, b.height, comp.label, b.id);
  });
  for (const c of reference.reference_connections) {
    const from = boxById.get(c.source);
    const to = boxById.get(c.target);
    if (!from || !to || from === to) continue;
    skeleton.push({
      type: "arrow",
      ...arrowGeometry(from, to),
      start: { id: c.source },
      end: { id: c.target },
      ...(c.label ? { label: { text: c.label, fontSize: 14 } } : {}),
    });
  }
  return convertToExcalidrawElements(skeleton, { regenerateIds: false });
}

export default function DesignCanvas({
  initialElements,
  reference,
  readOnly = false,
  onChange,
  onReady,
}: {
  /** Saved scene elements (the candidate's diagram). */
  initialElements?: readonly ExcalidrawElement[];
  /** Render this reference design instead (read-only report view). */
  reference?: ReferenceBrief;
  readOnly?: boolean;
  /** Called with the scene's live elements as JSON when they change. */
  onChange?: (elementsJson: string) => void;
  onReady?: (handle: DesignCanvasHandle) => void;
}) {
  const apiRef = useRef<ExcalidrawImperativeAPI | null>(null);
  const versionRef = useRef<number | null>(null);
  const insertCountRef = useRef(0);

  const initialData = useMemo<ExcalidrawInitialDataState>(
    () => ({
      elements: reference
        ? referenceElements(reference)
        : (initialElements ?? []),
      // Leave viewBackgroundColor at its default — the dark theme inverts
      // canvas colors, so white is what renders dark.
      scrollToContent: true,
    }),
    // Excalidraw reads initialData once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const setApi = useCallback(
    (api: ExcalidrawImperativeAPI) => {
      apiRef.current = api;
      if (readOnly) {
        // Read-only views (the report) start zoomed to fit the whole design.
        setTimeout(() => {
          const elements = api.getSceneElements();
          if (elements.length) {
            api.scrollToContent(elements, { fitToContent: true });
          }
        }, 0);
      }
      onReady?.({
        addComponent(item) {
          const appState = api.getAppState();
          const center = viewportCoordsToSceneCoords(
            {
              clientX: appState.offsetLeft + appState.width / 2,
              clientY: appState.offsetTop + appState.height / 2,
            },
            appState,
          );
          // Nudge consecutive inserts so they don't stack exactly.
          const nudge = (insertCountRef.current++ % 6) * 24;
          const created = convertToExcalidrawElements([
            paletteSkeleton(
              item,
              center.x - BOX_WIDTH / 2 + nudge,
              center.y - BOX_HEIGHT / 2 + nudge,
            ),
          ]);
          api.updateScene({
            elements: [...api.getSceneElementsIncludingDeleted(), ...created],
            appState: { selectedElementIds: { [created[0].id]: true } },
            captureUpdate: CaptureUpdateAction.IMMEDIATELY,
          });
        },
        focusElements(ids) {
          const wanted = new Set(ids);
          const found = api.getSceneElements().filter((el) => wanted.has(el.id));
          if (!found.length) return;
          api.updateScene({
            appState: {
              selectedElementIds: Object.fromEntries(
                found.map((el) => [el.id, true as const]),
              ),
            },
          });
          api.scrollToContent(found, { fitToContent: true, animate: true });
        },
      });
    },
    [onReady, readOnly],
  );

  return (
    <div className="whiteboard h-full w-full overflow-hidden rounded-lg border border-white/[.08]">
      <Excalidraw
        excalidrawAPI={setApi}
        initialData={initialData}
        theme="dark"
        viewModeEnabled={readOnly}
        UIOptions={{
          canvasActions: {
            loadScene: false,
            saveToActiveFile: false,
            export: false,
            toggleTheme: false,
            changeViewBackgroundColor: false,
          },
          tools: { image: false },
        }}
        onChange={(elements) => {
          if (!onChange) return;
          const version = getSceneVersion(elements);
          // The first call reports the scene as loaded — not an edit.
          if (versionRef.current === null) {
            versionRef.current = version;
            return;
          }
          if (version === versionRef.current) return;
          versionRef.current = version;
          onChange(JSON.stringify(elements.filter((el) => !el.isDeleted)));
        }}
      />
    </div>
  );
}
