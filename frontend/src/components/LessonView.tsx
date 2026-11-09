import parse, { Element, type DOMNode, type HTMLReactParserOptions } from "html-react-parser";
import { marked } from "marked";
import type { Block, Lesson, Unit } from "../types";
import { Widget } from "./widgets";

/** Renders trusted HTML from content/ and mounts <div data-widget="..."> placeholders as React widgets. */
function HtmlContent({ html, unit }: { html: string; unit: Unit }) {
  const options: HTMLReactParserOptions = {
    replace(node: DOMNode) {
      if (node instanceof Element && node.attribs["data-widget"]) {
        let props: Record<string, unknown> = {};
        try { props = node.attribs["data-props"] ? JSON.parse(node.attribs["data-props"]) : {}; } catch { /* keep defaults */ }
        return <Widget name={node.attribs["data-widget"]} props={props} unit={unit} />;
      }
      return undefined;
    },
  };
  return <>{parse(html, options)}</>;
}

function BlockView({ block, unit }: { block: Block; unit: Unit }) {
  switch (block.type) {
    case "html":
      return <HtmlContent html={block.content} unit={unit} />;
    case "markdown":
      return <div className="box md"><HtmlContent html={marked.parse(block.content ?? block.text ?? "", { async: false })} unit={unit} /></div>;
    case "widget":
      return <Widget name={block.widget} props={block.props} unit={unit} />;
    default:
      return null;
  }
}

export function LessonView({ lesson, unit }: { lesson: Lesson; unit: Unit }) {
  return (
    <section className="mlearn">
      {lesson.blocks.map((b, i) => <BlockView key={i} block={b} unit={unit} />)}
    </section>
  );
}
