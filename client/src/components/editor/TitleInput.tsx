import { useEffect, useState } from 'react';
import { DEFAULT_DOC_TITLE, TITLE_MAX_LENGTH } from '../../utils/constants';

interface TitleInputProps {
  value: string;
  disabled?: boolean;
  onChange: (title: string) => void;
  onEnter?: () => void;
  autoFocus?: boolean;
}

/** Inline-editable document title. Empty titles are never sent; blur restores a default. */
export default function TitleInput({ value, disabled, onChange, onEnter, autoFocus }: TitleInputProps) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);

  return (
    <input
      type="text"
      aria-label="Document title"
      value={draft}
      disabled={disabled}
      maxLength={TITLE_MAX_LENGTH}
      autoFocus={autoFocus}
      onFocus={(e) => autoFocus && e.target.select()}
      onChange={(e) => {
        setDraft(e.target.value);
        if (e.target.value.trim()) onChange(e.target.value.trim());
      }}
      onBlur={() => {
        if (!draft.trim()) {
          setDraft(DEFAULT_DOC_TITLE);
          onChange(DEFAULT_DOC_TITLE);
        }
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          (e.target as HTMLInputElement).blur();
          onEnter?.();
        }
      }}
      className="w-full min-w-0 truncate rounded-md border border-transparent px-2 py-1 text-base font-medium text-slate-900 hover:border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none disabled:bg-transparent disabled:text-slate-900 disabled:hover:border-transparent"
    />
  );
}
