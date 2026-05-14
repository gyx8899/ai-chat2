// useImageUpload hook - 占位实现
// TODO: 后续实现完整的图片上传功能

import { useState, useRef, useCallback } from 'react'
import type { ImageAttachment } from '@/types'

export function useImageUpload() {
  const [attachments, setAttachments] = useState<ImageAttachment[]>([])
  const [isUploading, _setIsUploading] = useState(false) // eslint-disable-line @typescript-eslint/no-unused-vars
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const hasAttachment = attachments.length > 0

  const addAttachment = (attachment: ImageAttachment) => {
    setAttachments((prev) => [...prev, attachment])
  }

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id))
  }

  const clearAttachments = () => {
    setAttachments([])
  }

  // 添加文件的便捷方法
  const addFiles = (files: File[]) => {
    const newAttachments: ImageAttachment[] = files.map((file, idx) => ({
      id: `${Date.now()}-${idx}`,
      dataUrl: URL.createObjectURL(file),
      name: file.name,
      size: file.size,
    }))
    setAttachments((prev) => [...prev, ...newAttachments])
  }

  // 按索引移除
  const removeAt = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index))
  }

  // 清除所有
  const clearAll = () => {
    setAttachments([])
  }

  // 拖拽处理
  const dragHandlers = {
    onDragOver: useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(true)
    }, []),
    onDragLeave: useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
    }, []),
    onDrop: useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
      if (files.length > 0) {
        addFiles(files)
      }
    }, []),
  }

  // 触发文件选择
  const triggerFileSelect = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(f => f.type.startsWith('image/'))
    if (files.length > 0) {
      addFiles(files)
    }
    // 重置 input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  return {
    attachments,
    isUploading,
    hasAttachment,
    addAttachment,
    removeAttachment,
    clearAttachments,
    addFiles,
    removeAt,
    clearAll,
    dragOver,
    dragHandlers,
    fileInputRef,
    triggerFileSelect,
    handleFileSelect,
  }
}