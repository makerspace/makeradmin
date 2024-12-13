import React, { useState } from "react";

const FileInput = () => {
    const [filename, setFilename] = useState("");

    const clearUpload = () => {
        setFilename("");
    };

    return (
        <div>
            <div id="upload-drop" className="uk-placeholder">
                <p>
                    <i className="uk-icon-cloud-upload uk-icon-medium uk-text-muted uk-margin-small-right"></i>
                    {filename ? (
                        <span>
                            {filename} (<a onClick={clearUpload}>Ta bort</a>)
                        </span>
                    ) : (
                        <span>
                            Ladda upp genom att dra och släppa en fil här eller
                            klicka på{" "}
                            <a className="uk-form-file">
                                ladda upp
                                <input
                                    id="upload-select"
                                    className="uk-hidden"
                                    type="file"
                                />
                            </a>
                            .
                        </span>
                    )}
                </p>
            </div>
        </div>
    );
};

export default FileInput;
