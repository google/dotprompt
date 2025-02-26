import clsx from "clsx";
import type { Message } from "dotprompt";
import Markdown from "react-markdown";

const SHARED_CLASSES = ["rounded-xl", "my-4", "p-4"];

function roleClasses(role: Message["role"]) {
  if (role === "system") return ["bg-background", "border", "border-2", "text-accent-foreground"];
  if (["model", "tool"].includes(role))
    return ["bg-primary", "text-primary-foreground", "mr-10", "rounded-tl-none"];
  if (role === "user")
    return ["bg-secondary", "text-secondary-foreground", "ml-10", "rounded-tr-none"];
  return [];
}

export default function MessageCard({ message }: { message: Message }) {
  message = { role: message.role || "user", content: message.content || [] };
  const text = message.content.map((p) => p.text || "").join("");
  const toolRequests = message.content.filter((p) => !!p.toolRequest);
  const toolResponses = message.content.filter((p) => !!p.toolResponse);
  // const media = // TODO

  return (
    <div className={clsx(...SHARED_CLASSES, ...roleClasses(message.role))}>
      <h4 className="uppercase text-xs text-primary-foreground opacity-70 mb-1">{message.role}</h4>
      {text && (
        <Markdown
          className={
            "prose text-inherit prose-strong:text-inherit prose-sm prose-pre:bg-black prose-pre:text-white prose-li:ps-0 prose-li:m-0 prose-p:mb-1 prose-ul:mt-2"
          }
        >
          {text}
        </Markdown>
      )}
      {toolRequests.length > 0 &&
        toolRequests.map((t) => (
          <pre className="border rounded p-4">{JSON.stringify(t.toolRequest, null, 2)}</pre>
        ))}
      {toolResponses.length > 0 &&
        toolResponses.map((t) => (
          <pre className="border rounded p-4">{JSON.stringify(t.toolResponse, null, 2)}</pre>
        ))}
    </div>
  );
}
