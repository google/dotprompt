import ReactMarkdown from 'react-markdown';
import type { Options } from 'react-markdown';

export default function Markdown({ children, ...props }: Options) {
  return (
    <ReactMarkdown {...props}>{children?.replace(/\n/g, '  \n')}</ReactMarkdown>
  );
}
