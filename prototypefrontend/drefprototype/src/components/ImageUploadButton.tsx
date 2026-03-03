import { useState, useRef } from "react";
import { ImagePlus, X } from "lucide-react";

interface ImageUploadButtonProps {
  label?: string;
  accept?: string;
  maxFiles?: number;
}

const ImageUploadButton = ({
  label = "Select an Image",
  accept = "image/*",
  maxFiles = 1,
}: ImageUploadButtonProps) => {
  const [files, setFiles] = useState<{ name: string; url: string }[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected) return;

    const newFiles = Array.from(selected)
      .slice(0, maxFiles - files.length)
      .map((f) => ({ name: f.name, url: URL.createObjectURL(f) }));

    setFiles((prev) => [...prev, ...newFiles].slice(0, maxFiles));
    // Reset so same file can be re-selected
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setFiles((prev) => {
      URL.revokeObjectURL(prev[index].url);
      return prev.filter((_, i) => i !== index);
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex items-center gap-2 rounded-full border border-primary px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
          disabled={files.length >= maxFiles}
        >
          <ImagePlus className="h-4 w-4" />
          {label}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={maxFiles > 1}
          onChange={handleChange}
          className="hidden"
        />
        {files.length === 0 && (
          <p className="text-xs text-muted-foreground">No file selected</p>
        )}
      </div>

      {files.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {files.map((file, i) => (
            <div key={i} className="relative group">
              <img
                src={file.url}
                alt={file.name}
                className="h-20 w-20 rounded-full border border-border object-cover"
              />
              <button
                type="button"
                onClick={() => removeFile(i)}
                className="absolute -right-2 -top-2 rounded-full bg-destructive p-0.5 text-destructive-foreground opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X className="h-3 w-3" />
              </button>
              <p className="mt-1 max-w-[80px] truncate text-[10px] text-muted-foreground">
                {file.name}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ImageUploadButton;
