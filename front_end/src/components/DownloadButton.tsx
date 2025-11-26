import { useState } from 'react';
import './DownloadButton.css';

interface DownloadButtonProps {
  materialId: string;
  fileName: string;
  fileType: 'pdf' | 'doc' | 'ppt' | 'video' | 'image' | 'other';
  fileSize?: string;
  onDownload?: (materialId: string) => Promise<void>;
}

export function DownloadButton({ 
  materialId, 
  fileName, 
  fileType, 
  fileSize,
  onDownload 
}: DownloadButtonProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const getFileIcon = (type: string) => {
    const icons = {
      pdf: '📄',
      doc: '📝',
      ppt: '📊',
      video: '🎬',
      image: '🖼️',
      other: '📎'
    };
    return icons[type as keyof typeof icons] || icons.other;
  };

  const getFileColor = (type: string) => {
    const colors = {
      pdf: '#FF6B6B',
      doc: '#4ECDC4',
      ppt: '#45B7D1',
      video: '#96CEB4',
      image: '#FECA57',
      other: '#95A5A6'
    };
    return colors[type as keyof typeof colors] || colors.other;
  };

  const handleDownload = async () => {
    if (isDownloading) return;
    
    setIsDownloading(true);
    setDownloadProgress(0);
    
    try {
      // Simulate download progress
      const interval = setInterval(() => {
        setDownloadProgress(prev => {
          if (prev >= 95) {
            clearInterval(interval);
            return 95;
          }
          return prev + 5;
        });
      }, 100);

      if (onDownload) {
        await onDownload(materialId);
      } else {
        // Default download logic
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      clearInterval(interval);
      setDownloadProgress(100);
      
      // Download complete animation
      setTimeout(() => {
        setIsDownloading(false);
        setDownloadProgress(0);
      }, 1000);
      
    } catch (error) {
      console.error('Download failed:', error);
      setIsDownloading(false);
      setDownloadProgress(0);
    }
  };

  return (
    <div className="download-button-container">
      <div className="file-info">
        <div 
          className="file-icon" 
          style={{ backgroundColor: getFileColor(fileType) }}
        >
          {getFileIcon(fileType)}
        </div>
        <div className="file-details">
          <div className="file-name">{fileName}</div>
          {fileSize && <div className="file-size">{fileSize}</div>}
        </div>
      </div>
      
      <button
        className={`download-btn ${isDownloading ? 'downloading' : ''}`}
        onClick={handleDownload}
        disabled={isDownloading}
        aria-label={`Download ${fileName}`}
      >
        {isDownloading ? (
          <>
            <div className="download-progress">
              <div 
                className="progress-bar" 
                style={{ width: `${downloadProgress}%` }}
              ></div>
            </div>
            <span className="download-text">
              {downloadProgress === 100 ? '✅' : '⏳'} 
              {downloadProgress === 100 ? 'Complete' : `${downloadProgress}%`}
            </span>
          </>
        ) : (
          <>
            <span className="download-icon">⬇️</span>
            <span className="download-text">Download</span>
          </>
        )}
      </button>
    </div>
  );
}