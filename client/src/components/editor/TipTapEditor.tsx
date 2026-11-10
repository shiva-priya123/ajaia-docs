import Placeholder from '@tiptap/extension-placeholder';
import Underline from '@tiptap/extension-underline';
import { EditorContent, useEditor, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { useEffect, useRef, type ReactNode } from 'react';
import { parseDocContent } from '../../utils/docText';
import EditorToolbar from './EditorToolbar';

interface TipTapEditorProps {
  /** Initial TipTap JSON (string, as stored). Only read on mount. */
  initialContent: string | null;
  editable: boolean;
  onChange: (json: string) => void;
  onReady?: (editor: Editor) => void;
  /** Rendered above the page, under the toolbar (e.g. banners). */
  banner?: ReactNode;
}

export default function TipTapEditor({ initialContent, editable, onChange, onReady, banner }: TipTapEditorProps) {
  // Callbacks are captured once by the editor; route them through refs so they stay current.
  const onChangeRef = useRef(onChange);
  const onReadyRef = useRef(onReady);
  onChangeRef.current = onChange;
  onReadyRef.current = onReady;

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Placeholder.configure({ placeholder: 'Start writing…' }),
    ],
    content: parseDocContent(initialContent),
    editable,
    editorProps: {
      attributes: { 'aria-label': 'Document content', role: 'textbox', 'aria-multiline': 'true' },
    },
    onUpdate: ({ editor: e }) => onChangeRef.current(JSON.stringify(e.getJSON())),
    onCreate: ({ editor: e }) => onReadyRef.current?.(e),
  });

  useEffect(() => {
    if (editor && editor.isEditable !== editable) editor.setEditable(editable);
  }, [editor, editable]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {editable && editor && (
        <div className="sticky top-14 z-20 border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-4xl px-4 py-1.5 sm:px-6">
            <EditorToolbar editor={editor} />
          </div>
        </div>
      )}
      <div className="flex-1 bg-slate-100/70 px-2 py-6 sm:px-6 sm:py-10">
        <div className="mx-auto max-w-[816px] space-y-4">
          {banner}
          <div
            className="doc-content min-h-[70vh] cursor-text rounded-sm bg-white px-6 py-10 shadow-sm ring-1 ring-slate-200 sm:px-16 sm:py-14"
            onClick={() => editable && editor?.chain().focus().run()}
          >
            <EditorContent editor={editor} />
          </div>
        </div>
      </div>
    </div>
  );
}
