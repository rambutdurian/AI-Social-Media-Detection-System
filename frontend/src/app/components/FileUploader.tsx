import { useState, useRef } from 'react';
import { Upload, X, FileVideo, Image as ImageIcon, Link2, AlertCircle } from 'lucide-react';

interface FileUploaderProps {
  onFileSelect: (file: File, type: 'image' | 'video') => void;
  onUrlSubmit: (url: string) => void;
}

export function FileUploader({ onFileSelect, onUrlSubmit }: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ file: File; type: 'image' | 'video'; preview?: string }>>([]);
  const [url, setUrl] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFiles = (files: FileList) => {
    Array.from(files).forEach(file => {
      const type = file.type.startsWith('image/') ? 'image' : file.type.startsWith('video/') ? 'video' : null;

      if (type) {
        const preview = type === 'image' ? URL.createObjectURL(file) : undefined;
        setUploadedFiles(prev => [...prev, { file, type, preview }]);
        onFileSelect(file, type);
      }
    });
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => {
      const newFiles = [...prev];
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview!);
      }
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const handleUrlSubmit = () => {
    if (url.trim()) {
      onUrlSubmit(url);
      setUrl('');
    }
  };

  return (
    <div className="space-y-4">
      {/* URL Input */}
      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/20">
        <label className="block text-white mb-2 flex items-center gap-2">
          <Link2 className="w-4 h-4" />
          Paste URL Link
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/suspicious-content"
            className="flex-1 px-4 py-2 bg-white/90 text-gray-900 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
          />
          <button
            onClick={handleUrlSubmit}
            disabled={!url.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all"
          >
            Add URL
          </button>
        </div>
      </div>

      {/* File Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 transition-all ${
          dragActive
            ? 'border-blue-400 bg-blue-500/10'
            : 'border-white/30 bg-white/5 hover:border-white/50 hover:bg-white/10'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="text-center">
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-white mb-2">Drag & drop images or videos here</p>
          <p className="text-gray-400 text-sm mb-4">or</p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-6 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 transition-all border border-white/30"
          >
            Browse Files
          </button>
          <p className="text-gray-500 text-xs mt-4">Supports: JPG, PNG, GIF, MP4, MOV, AVI</p>
        </div>
      </div>

      {/* Uploaded Files Preview */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/20">
          <h3 className="text-white mb-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Uploaded Files ({uploadedFiles.length})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {uploadedFiles.map((item, index) => (
              <div
                key={index}
                className="relative group rounded-lg overflow-hidden bg-white/10 border border-white/20"
              >
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-1 right-1 p-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-10"
                >
                  <X className="w-3 h-3 text-white" />
                </button>

                {item.type === 'image' ? (
                  <div className="aspect-square">
                    <img
                      src={item.preview}
                      alt={item.file.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="aspect-square flex items-center justify-center bg-gray-800">
                    <FileVideo className="w-8 h-8 text-gray-400" />
                  </div>
                )}

                <div className="p-2 bg-gray-900/80">
                  <p className="text-white text-xs truncate">{item.file.name}</p>
                  <p className="text-gray-400 text-xs">
                    {(item.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
