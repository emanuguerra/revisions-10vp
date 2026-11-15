import parse, { domToReact, Element, type DOMNode, type HTMLReactParserOptions } from "html-react-parser";
import { marked } from "marked";
import { Link } from "react-router-dom";
import type { Block, Lesson, Unit } from "../types";
import { Widget } from "./widgets";

/** Renders trusted HTML from content/ and mounts <div data-widget="..."> placeholders as React widgets.
 *  Links written `wiki:<path>` open a page of the knowledge base. Without a unit, widgets are not shown. */
export function HtmlContent({ html, unit }: { html: string; unit: Unit | null }) {
  const options: HTMLReactParserOptions = {
    replace(node: DOMNode) {
      if (node instanceof Element && node.name === "a" && node.attribs.href?.startsWith("wiki:")) {
        return <Link to={`/wiki/${node.attribs.href.slice(5)}`}>{domToReact(node.children as DOMNode[], options)}</Link>;
      }
      if (node instanceof Element && node.attribs["data-widget"]) {
        if (!unit) return <p className="muted">(Exercice interactif : ouvre la leçon pour l'utiliser.)</p>;
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
