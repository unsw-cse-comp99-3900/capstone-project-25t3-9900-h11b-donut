import { useEffect, useMemo, useRef, useState } from "react";

type Props = {
  value?: File | null;                     
  onChange?: (file: File | null) => void;  
  initialUrl?: string | null;              
  size?: number;                           
  maxMB?: number;                        
};

export default function AvatarPicker({
  value,
  onChange,
  initialUrl = null,
  size = 96,
  maxMB = 2,
}: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [, setFile] = useState<File | null>(value ?? null);
  const [err, setErr] = useState("");
  const [localUrl, setLocalUrl] = useState<string | null>(null);


  useEffect(() => { if (value !== undefined) setFile(value ?? null); }, [value]);


  const preview = useMemo(() => localUrl ?? initialUrl ?? "/default-avatar.png", [localUrl, initialUrl]);


  useEffect(() => () => { if (localUrl) URL.revokeObjectURL(localUrl); }, [localUrl]);

  const pick = (f?: File) => {
    setErr("");
    if (!f) { setFile(null); setLocalUrl(null); onChange?.(null); return; }

    const okType = ["image/jpeg", "image/jpg", "image/png"].includes(f.type);
    if (!okType) { setErr("only accept .jpg / .png pic"); return; }
    if (f.size > maxMB * 1024 * 1024) { setErr(`no larger than ${maxMB}MB`); return; }

    const url = URL.createObjectURL(f);
    setFile(f);
    setLocalUrl(url);
    onChange?.(f);
  };

  return (
    <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <button
  type="button"
  onClick={() => inputRef.current?.click()}
  title="Click to upload"
  style={{
    width: size,
    height: size,
    borderRadius: "50%",
    border: "1px solid #ddd",
    background: "#fafafa",
    overflow: "hidden",
    cursor: "pointer",
    padding: 0,
    position: "relative",    
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  }}
>
  {localUrl || initialUrl ? (
    <img
      src={preview}
      alt="avatar"
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  ) : (
    
    <span style={{ fontSize: 32, color: "#999", lineHeight: 1 }}>＋</span>
  )}
</button>


      <input
        ref={inputRef}
        type="file"
        accept="image/png, image/jpeg"
        style={{ display: "none" }}
        onChange={(e) => pick(e.target.files?.[0] ?? undefined)}
      />

      <div style={{ fontSize: 12, color: "#666" }}>JPG/PNG WITH MAX {maxMB} MB</div>
      {err && <div style={{ fontSize: 12, color: "#d33" }}>{err}</div>}
    </div>
  );
}
