import type { Editor } from '@tiptap/react';
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Quote,
  Redo2,
  Strikethrough,
  Underline as UnderlineIcon,
  Undo2,
  type LucideIcon,
} from 'lucide-react';

type BlockType = 'paragraph' | 'h1' | 'h2' | 'h3';

function currentBlock(editor: Editor): BlockType {
  for (const level of [1, 2, 3] as const) {
    if (editor.isActive('heading', { level })) return `h${level}`;
  }
  return 'paragraph';
}

function setBlock(editor: Editor, value: BlockType) {
  const chain = editor.chain().focus();
  if (value === 'paragraph') chain.setParagraph().run();
  else chain.setHeading({ level: Number(value.slice(1)) as 1 | 2 | 3 }).run();
}

interface ToolButtonProps {
  icon: LucideIcon;
  label: string;
  shortcut?: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
}

function ToolButton({ icon: Icon, label, shortcut, active, disabled, onClick }: ToolButtonProps) {
  return (
    <button
      type="button"
      onMouseDown={(e) => e.preventDefault() /* keep the editor selection */}
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      aria-pressed={active}
      title={shortcut ? `${label} (${shortcut})` : label}
      className={`shrink-0 rounded-md p-1.5 transition disabled:opacity-40 ${
        active ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
      }`}
    >
      <Icon className="h-4 w-4" aria-hidden />
    </button>
  );
}

const Divider = () => <span className="mx-1 h-5 w-px shrink-0 bg-slate-200" aria-hidden />;

export default function EditorToolbar({ editor }: { editor: Editor }) {
  const mod = typeof navigator !== 'undefined' && /Mac/i.test(navigator.platform) ? '⌘' : 'Ctrl';

  return (
    <div role="toolbar" aria-label="Formatting" className="flex items-center gap-0.5 overflow-x-auto max-sm:-mx-1 max-sm:px-1">
      <select
        aria-label="Text style"
        value={currentBlock(editor)}
        onChange={(e) => setBlock(editor, e.target.value as BlockType)}
        className="mr-1 shrink-0 rounded-md border border-slate-200 bg-white py-1 pr-7 pl-2 text-sm text-slate-700 hover:border-slate-300 focus:border-blue-500 focus:outline-none"
      >
        <option value="paragraph">Normal text</option>
        <option value="h1">Heading 1</option>
        <option value="h2">Heading 2</option>
        <option value="h3">Heading 3</option>
      </select>
      <Divider />
      <ToolButton icon={Bold} label="Bold" shortcut={`${mod}+B`} active={editor.isActive('bold')} onClick={() => editor.chain().focus().toggleBold().run()} />
      <ToolButton icon={Italic} label="Italic" shortcut={`${mod}+I`} active={editor.isActive('italic')} onClick={() => editor.chain().focus().toggleItalic().run()} />
      <ToolButton icon={UnderlineIcon} label="Underline" shortcut={`${mod}+U`} active={editor.isActive('underline')} onClick={() => editor.chain().focus().toggleUnderline().run()} />
      <ToolButton icon={Strikethrough} label="Strikethrough" active={editor.isActive('strike')} onClick={() => editor.chain().focus().toggleStrike().run()} />
      <Divider />
      <ToolButton icon={List} label="Bulleted list" active={editor.isActive('bulletList')} onClick={() => editor.chain().focus().toggleBulletList().run()} />
      <ToolButton icon={ListOrdered} label="Numbered list" active={editor.isActive('orderedList')} onClick={() => editor.chain().focus().toggleOrderedList().run()} />
      <ToolButton icon={Quote} label="Quote" active={editor.isActive('blockquote')} onClick={() => editor.chain().focus().toggleBlockquote().run()} />
      <Divider />
      <ToolButton icon={Undo2} label="Undo" shortcut={`${mod}+Z`} disabled={!editor.can().undo()} onClick={() => editor.chain().focus().undo().run()} />
      <ToolButton icon={Redo2} label="Redo" shortcut={`${mod}+Shift+Z`} disabled={!editor.can().redo()} onClick={() => editor.chain().focus().redo().run()} />
    </div>
  );
}
