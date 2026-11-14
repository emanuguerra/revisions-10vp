// Widgets usable in lessons: `{type: widget, widget: <name>, props: {...}}` in unit.yaml,
// or `<div data-widget="<name>" data-props='{...}'></div>` inside an html/markdown block.
import type { ComponentType } from "react";
import type { Unit } from "../../types";
import { AlbedoExplorer, ClimographExplorer } from "./ClimateWidgets";
import { DistributivityExplorer } from "./DistributivityExplorer";
import { ForceAdder } from "./ForceFigure";
import { PythagoreExplorer } from "./PythagoreExplorer";
import { SoundCheck } from "./SoundCheck";
import { TriangleFigure } from "./TriangleFigure";
import { TriangleTester } from "./TriangleTester";
import { VocabCards } from "./VocabCards";
import { MemoryGame } from "./MemoryGame";
import { WortCards } from "./WortCards";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const WIDGETS: Record<string, ComponentType<any>> = {
  "triangle-figure": TriangleFigure,
  "pythagore-explorer": PythagoreExplorer,
  "triangle-tester": TriangleTester,
  "sound-check": SoundCheck,
  "vocab-cards": VocabCards,
  "distributivity-explorer": DistributivityExplorer,
  "wort-cards": WortCards,
  "memory-game": MemoryGame,
  "climograph-explorer": ClimographExplorer,
  "albedo-explorer": AlbedoExplorer,
  "force-adder": ForceAdder,
};

export function Widget({ name, props, unit }: { name: string; props?: Record<string, unknown>; unit: Unit }) {
  const C = WIDGETS[name];
  if (!C) return <p className="muted">Widget inconnu : {name}</p>;
  return <C unit={unit} {...props} />;
}
