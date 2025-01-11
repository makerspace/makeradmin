import React from "react";

type ButtonProps = {
    children: React.ReactNode;
    onClick: () => void;
    style?: React.CSSProperties;
};

export const Button = (props: ButtonProps) => {
    return (
        <button
            onClick={props.onClick}
            // TODO: Use UiKit styling
            style={{
                backgroundColor: "#333333" /* Dark grey */,
                border: "none",
                color: "white",
                padding: "15px 10px",
                textAlign: "center",
                textDecoration: "none",
                display: "inline-block",
                fontSize: "16px",
                margin: "10px 2px",
                cursor: "pointer",
                width: "300px",
                ...props.style,
            }}
        >
            {props.children}
        </button>
    );
};
