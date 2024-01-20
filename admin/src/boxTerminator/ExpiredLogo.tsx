import React from "react";

type ExpiredLogoProps = {
    width?: string;
};

export const ExpiredLogo = (props: ExpiredLogoProps) => {
    return (
        <svg
            width={props.width || "800px"}
            height={props.width || "800px"}
            viewBox="0 0 48 48"
            xmlns="http://www.w3.org/2000/svg"
            style={{ fill: "#e54141" }}
        >
            <title>expire-solid</title>
            <g id="Layer_2" data-name="Layer 2">
                <g id="icons_Q2" data-name="icons Q2">
                    <g>
                        <rect width="48" height="48" fill="none" />
                        <g>
                            <path d="M14.2,31.9h0a2,2,0,0,0-.9-2.9A11.8,11.8,0,0,1,6.1,16.8,12,12,0,0,1,16.9,6a12.1,12.1,0,0,1,11.2,5.6,2.3,2.3,0,0,0,2.3.9h0a2,2,0,0,0,1.1-3,15.8,15.8,0,0,0-15-7.4,16,16,0,0,0-4.8,30.6A2,2,0,0,0,14.2,31.9Z" />
                            <path d="M16.5,11.5v5h-5a2,2,0,0,0,0,4h9v-9a2,2,0,0,0-4,0Z" />
                            <path d="M45.7,43l-15-26a2,2,0,0,0-3.4,0l-15,26A2,2,0,0,0,14,46H44A2,2,0,0,0,45.7,43ZM29,42a2,2,0,1,1,2-2A2,2,0,0,1,29,42Zm2-8a2,2,0,0,1-4,0V26a2,2,0,0,1,4,0Z" />
                        </g>
                    </g>
                </g>
            </g>
        </svg>
    );
};
