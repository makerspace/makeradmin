import React, { useEffect, useRef } from "react";
import auth from "../auth";

export interface Upload {
    id: number;
    category: string;
    name: string;
    type: string;
    width: number;
    height: number;
    url: string;
}

interface PasteImageHandlerProps {
    textAreaRef: React.RefObject<HTMLTextAreaElement>;
    onUploadComplete: (result: Upload) => void;
    category?: string; // Category for the upload (default: "quiz")
    model?: any; // Model to update directly (for Textarea components)
    fieldName?: string; // Field name in the model
    onUploadStart?: () => void;
    onUploadError?: (error: string) => void;
}

/**
 * Component that intercepts paste and drag-drop events in text areas to handle image uploads.
 *
 * Uploads to /storage/image and inserts <img> tag at cursor position.
 */
export const PasteImageHandler: React.FC<PasteImageHandlerProps> = ({
    textAreaRef,
    onUploadComplete,
    category = "quiz",
    model,
    fieldName,
    onUploadStart,
    onUploadError,
}) => {
    const uploadingRef = useRef(false);

    useEffect(() => {
        const textarea = textAreaRef.current;
        if (!textarea) return;

        const handleImageUpload = async (imageFile: File) => {
            // Don't start a new upload if one is in progress
            if (uploadingRef.current) {
                console.warn("Upload already in progress");
                return;
            }

            uploadingRef.current = true;
            onUploadStart?.();

            try {
                // Read file as base64
                const base64Data = await fileToBase64(imageFile);

                // Upload to generic storage endpoint using fetch directly
                // (bypassing gateway to handle errors ourselves)
                const accessToken = auth.getAccessToken();
                const response = await fetch(
                    `${config.apiBasePath}/storage/image`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json; charset=UTF-8",
                            ...(accessToken
                                ? { Authorization: `Bearer ${accessToken}` }
                                : {}),
                        },
                        body: JSON.stringify({
                            category: category,
                            name: imageFile.name,
                            type: imageFile.type,
                            data: base64Data,
                        }),
                    },
                );

                let responseData;
                try {
                    responseData = await response.json();
                } catch (e) {
                    // Server didn't return JSON (e.g., returned HTML error page)
                    throw new Error("Serverfel vid bilduppladdning");
                }

                if (!response.ok) {
                    // Extract error message from response
                    let errorMessage = "Kunde inte ladda upp bilden";

                    if (responseData.message) {
                        errorMessage = responseData.message;
                    } else if (typeof responseData === "string") {
                        errorMessage = responseData;
                    }

                    throw new Error(errorMessage);
                }

                // Extract the actual data from the wrapped response
                // Backend returns: {"status": "ok", "data": {...}}
                const result: Upload = responseData.data;
                if (!result || !result.url) {
                    throw new Error("Ogiltigt svar från servern");
                }

                // Insert <img> tag at cursor position
                insertImageTagAtCursor(textarea, result.url, model, fieldName);

                onUploadComplete(result);
            } catch (error) {
                console.error("Failed to upload image:", error);
                const errorMessage =
                    error instanceof Error
                        ? error.message
                        : "Kunde inte ladda upp bilden";
                onUploadError?.(errorMessage);
            } finally {
                uploadingRef.current = false;
            }
        };

        const handlePaste = async (event: ClipboardEvent) => {
            const items = event.clipboardData?.items;
            if (!items) return;

            // Check if paste contains an image
            let imageFile: File | null = null;
            let hasNonImageFile = false;
            for (let i = 0; i < items.length; i++) {
                const item = items[i];
                if (item && item.type.startsWith("image/")) {
                    imageFile = item.getAsFile();
                    break;
                }
                if (item && item.kind === "file") {
                    hasNonImageFile = true;
                }
            }

            if (!imageFile) {
                // Only show error if user tried to paste a file (not text)
                if (hasNonImageFile) {
                    event.preventDefault();
                    onUploadError?.(
                        "Endast bildfiler kan laddas upp (PNG, JPG, GIF, WEBP)",
                    );
                }
                return;
            }

            // Prevent default paste behavior when we have an image
            event.preventDefault();

            await handleImageUpload(imageFile);
        };

        const handleDragOver = (event: DragEvent) => {
            // Check if drag contains files
            if (event.dataTransfer?.types.includes("Files")) {
                event.preventDefault();
                // Add visual feedback
                textarea.style.outline = "2px solid #0066cc";
                textarea.style.outlineOffset = "2px";
            }
        };

        const handleDragLeave = (event: DragEvent) => {
            // Only remove visual feedback if we're truly leaving the textarea
            // (not just hovering over a child element)
            if (
                event.relatedTarget &&
                textarea.contains(event.relatedTarget as Node)
            ) {
                return;
            }
            textarea.style.outline = "";
            textarea.style.outlineOffset = "";
        };

        const handleDrop = async (event: DragEvent) => {
            // Remove visual feedback
            textarea.style.outline = "";
            textarea.style.outlineOffset = "";

            const files = event.dataTransfer?.files;
            if (!files || files.length === 0) return;

            // Prevent default drop behavior for all files
            event.preventDefault();

            // Check if any file is an image
            let imageFile: File | null = null;
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                if (file && file.type.startsWith("image/")) {
                    imageFile = file;
                    break;
                }
            }

            if (!imageFile) {
                onUploadError?.(
                    "Endast bildfiler kan laddas upp (PNG, JPG, GIF, WEBP)",
                );
                return;
            }

            await handleImageUpload(imageFile);
        };

        textarea.addEventListener("paste", handlePaste);
        textarea.addEventListener("dragover", handleDragOver);
        textarea.addEventListener("dragleave", handleDragLeave);
        textarea.addEventListener("drop", handleDrop);

        return () => {
            textarea.removeEventListener("paste", handlePaste);
            textarea.removeEventListener("dragover", handleDragOver);
            textarea.removeEventListener("dragleave", handleDragLeave);
            textarea.removeEventListener("drop", handleDrop);
        };
    }, [
        onUploadComplete,
        textAreaRef,
        category,
        onUploadStart,
        onUploadError,
        model,
        fieldName,
    ]);

    // This component doesn't render anything
    return null;
};

/**
 * Convert a File to base64 string (without data URI prefix)
 */
function fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result as string;
            // Remove data URI prefix (e.g., "data:image/png;base64,")
            const parts = result.split(",");
            const base64 = parts[1];
            if (!base64) {
                reject(new Error("Failed to convert file to base64"));
                return;
            }
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

/**
 * Insert an <img> tag at the current cursor position in a textarea
 */
function insertImageTagAtCursor(
    textarea: HTMLTextAreaElement,
    imageUrl: string,
    model?: any,
    fieldName?: string,
) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;

    const imageTag = `<img src="${imageUrl}" alt="Uploaded image" />`;
    const newText = text.substring(0, start) + imageTag + text.substring(end);

    // Update the model directly if provided (for Textarea components)
    if (model && fieldName) {
        model[fieldName] = newText;
    } else {
        // Fallback to direct textarea manipulation
        textarea.value = newText;

        // Trigger change event so React/form state updates
        const event = new Event("input", { bubbles: true });
        textarea.dispatchEvent(event);
    }

    // Move cursor to after the inserted image tag
    const newCursorPos = start + imageTag.length;
    textarea.setSelectionRange(newCursorPos, newCursorPos);

    // Focus back on textarea
    textarea.focus();
}
