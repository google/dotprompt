import clsx from 'clsx';
import type { Message, Part } from 'dotprompt';
import Markdown from '@/components/markdown';

const SHARED_CLASSES = ['rounded-xl', 'my-4', 'p-4'];

function roleClasses(role: Message['role']) {
  if (role === 'system')
    return ['bg-background', 'border', 'border-2', 'text-accent-foreground'];
  if (['model', 'tool'].includes(role))
    return [
      'bg-primary',
      'text-primary-foreground',
      'mr-10',
      'rounded-tl-none',
    ];
  if (role === 'user')
    return [
      'bg-secondary',
      'text-secondary-foreground',
      'ml-10',
      'rounded-tr-none',
    ];
  return [];
}

function normalizeTextAndMedia(parts: Part[]) {
  return parts
    .filter((p) => p.text || p.media)
    .reduce((outParts, part) => {
      if (part.text && outParts.at(-1)?.text) {
        outParts.at(-1)!.text += part.text;
      } else {
        outParts.push(part);
      }
      return outParts;
    }, [] as Part[]);
}

export default function MessageCard({ message }: { message: Message }) {
  message = { role: message.role || 'user', content: message.content || [] };
  const textAndMedia = normalizeTextAndMedia(message.content);
  const toolRequests = message.content.filter((p) => !!p.toolRequest);
  const toolResponses = message.content.filter((p) => !!p.toolResponse);
  // const media = // TODO

  return (
    <div className={clsx(...SHARED_CLASSES, ...roleClasses(message.role))}>
      <h4 className="uppercase text-xs text-primary-foreground opacity-70 mb-1">
        {message.role}
      </h4>
      {textAndMedia.map((p, i) =>
        p.text ? (
          <Markdown
            key={i}
            className={
              'prose dark:prose-invert text-inherit prose-strong:text-inherit prose-sm prose-pre:bg-black prose-pre:text-white prose-li:ps-0 prose-li:m-0 prose-p:mb-1 prose-ul:mt-2 max-w-full'
            }
          >
            {p.text}
          </Markdown>
        ) : (
          <img
            key={i}
            className="max-w-96 max-h-96 object-contain rounded-lg my-4"
            src={p.media!.url}
          />
        ),
      )}
      {toolRequests.length > 0 &&
        toolRequests.map((t) => (
          <pre className="border rounded p-4">
            {JSON.stringify(t.toolRequest, null, 2)}
          </pre>
        ))}
      {toolResponses.length > 0 &&
        toolResponses.map((t) => (
          <pre className="border rounded p-4">
            {JSON.stringify(t.toolResponse, null, 2)}
          </pre>
        ))}
    </div>
  );
}
