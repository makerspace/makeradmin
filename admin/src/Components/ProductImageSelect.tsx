import classNames from "classnames/bind";
import React, { useEffect, useRef, useState } from "react";
import Select from "react-select";
import { get, post } from "../gateway";
import { notifyError, notifySuccess } from "../message";

interface ProductImageSelectProps {
    model: any;
    name: string;
    title: string;
    getLabel: (option: any) => React.ReactNode;
    getValue: (option: any) => number;
    nullOption?: { id: number };
}

const ProductImageSelect: React.FC<ProductImageSelectProps> = (props) => {
    const [options, setOptions] = useState<any[]>([]);
    const [isDirty, setIsDirty] = useState(false);
    const [value, setValue] = useState<number | null>(null);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const selectContainerRef = useRef<HTMLDivElement>(null);

    const UPLOAD_OPTION = {
        id: -1,
        name: "📤 Ladda upp ny bild...",
        type: "",
        data: "",
    };

    useEffect(() => {
        loadImages();
    }, []);

    const loadImages = () => {
        let newOptions: any[] = [];
        if (props.nullOption) {
            newOptions = [props.nullOption];
        }
        get({ url: "/webshop/product_image", params: { page_size: 0 } }).then(
            (data) => setOptions([UPLOAD_OPTION, ...newOptions, ...data.data]),
            () => null,
        );
    };

    useEffect(() => {
        const handleModelChange = () => {
            setValue(
                props.model[props.name] === null ? 0 : props.model[props.name],
            );
            setIsDirty(props.model.isDirty(props.name));
        };

        const unsubscribe = props.model.subscribe(handleModelChange);
        handleModelChange();

        return () => {
            unsubscribe();
        };
    }, [props.model, props.name]);

    const uploadImage = async (file: File) => {
        if (!file.type.startsWith("image/")) {
            notifyError("Endast bildfiler kan laddas upp");
            return;
        }

        setUploading(true);

        try {
            // Read file as base64
            const base64Data = await fileToBase64(file);

            // Upload image
            const response = await post({
                url: "/webshop/product_image",
                data: {
                    name: file.name,
                    type: file.type,
                    data: base64Data,
                },
            });

            if (response && response.data) {
                // Reload images to include the new one
                await loadImages();

                // Select the newly uploaded image
                props.model[props.name] = response.data.id;

                notifySuccess(`Bild "${file.name}" uppladdad`);
            }
        } catch (error) {
            console.error("Failed to upload image:", error);
            notifyError("Kunde inte ladda upp bilden");
        } finally {
            setUploading(false);
        }
    };

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            uploadImage(file);
        }
        // Reset file input
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleSelectChange = (option: any) => {
        if (option && option.id === UPLOAD_OPTION.id) {
            // Open file selector
            fileInputRef.current?.click();
        } else {
            props.model[props.name] = props.getValue(option);
        }
    };

    // Drag and drop handlers
    const handleDragOver = (event: React.DragEvent) => {
        if (event.dataTransfer?.types.includes("Files")) {
            event.preventDefault();
            event.stopPropagation();
            if (selectContainerRef.current) {
                selectContainerRef.current.style.outline = "2px solid #0066cc";
                selectContainerRef.current.style.outlineOffset = "2px";
            }
        }
    };

    const handleDragLeave = (event: React.DragEvent) => {
        if (selectContainerRef.current) {
            if (
                event.relatedTarget &&
                selectContainerRef.current.contains(event.relatedTarget as Node)
            ) {
                return;
            }
            selectContainerRef.current.style.outline = "";
            selectContainerRef.current.style.outlineOffset = "";
        }
    };

    const handleDrop = async (event: React.DragEvent) => {
        event.preventDefault();
        event.stopPropagation();

        if (selectContainerRef.current) {
            selectContainerRef.current.style.outline = "";
            selectContainerRef.current.style.outlineOffset = "";
        }

        const files = event.dataTransfer?.files;
        if (!files || files.length === 0) return;

        const file = files[0];
        if (file && file.type.startsWith("image/")) {
            await uploadImage(file);
        } else {
            notifyError("Endast bildfiler kan laddas upp");
        }
    };

    const classes = classNames(props.name, {
        changed: isDirty,
    });

    const currentValue = options.find((o) => o.id === value) || null;

    return (
        <div className={classes}>
            <label className="uk-form-label" htmlFor={props.name}>
                {props.title}
            </label>
            <div
                className="uk-form-controls"
                ref={selectContainerRef}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <Select
                    id={props.name}
                    name={props.name}
                    className="uk-width-1-1"
                    options={options}
                    value={currentValue}
                    getOptionValue={props.getValue}
                    getOptionLabel={props.getLabel}
                    onChange={handleSelectChange}
                    isDisabled={!options.length || uploading}
                    isLoading={uploading}
                />
                <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: "none" }}
                    accept="image/*"
                    onChange={handleFileSelect}
                />
            </div>
        </div>
    );
};

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

export default ProductImageSelect;
