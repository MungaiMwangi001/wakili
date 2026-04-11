"use client";
/** UploadZone – drag-and-drop file upload with animated feedback. */
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { documentsApi } from "@/lib/api";
import { useStore } from "@/store";

interface Props { onSuccess: () => void; }

export default function UploadZone({ onSuccess }: Props) {
  const t = useStore((s) => s.t);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState("");

  const onDrop = useCallback(async (accepted: File[]) => {
    if (!accepted.length) return;
    const file = accepted[0];
    setFileName(file.name);
    setUploading(true);
    try {
      await documentsApi.upload(file);
      toast.success(`"${file.name}" uploaded! Processing started.`);
      onSuccess();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      setFileName("");
    }
  }, [onSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"], "text/plain": [".txt"] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <motion.div
      {...getRootProps({ refKey: "ref" })}
      whileHover={{ scale: 1.01 }}
      className={`relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all
        ${isDragActive ? "border-accent bg-accent/10" : "border-primary/30 hover:border-primary bg-white hover:bg-primary/5"}`}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        {uploading ? (
          <motion.div key="uploading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="w-10 h-10 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-primary font-medium">{fileName}</p>
            <p className="text-gray-400 text-sm mt-1">Uploading & processing...</p>
          </motion.div>
        ) : (
          <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="text-5xl mb-4">{isDragActive ? "📂" : "📄"}</div>
            <p className="font-semibold text-gray-700">
              {isDragActive ? "Drop to upload!" : t("upload_drag")}
            </p>
            <p className="text-gray-400 text-sm mt-1">{t("upload_or")}</p>
            <button className="mt-3 px-5 py-2 rounded-xl bg-primary text-white text-sm font-medium hover:shadow-card transition-all">
              {t("upload_browse")}
            </button>
            <p className="text-xs text-gray-400 mt-3">{t("upload_formats")}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
