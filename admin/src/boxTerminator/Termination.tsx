import React from "react";

const { ExpiredLogo } = require("./ExpiredLogo.tsx");
const { ActiveLogo } = require("./ActiveLogo.tsx");

export type TerminationRenderProps = {
    type: string;
    member_number: number;
    member_name: string;
    expired: boolean;
    expiry_date: string;
    info: string | undefined;
    options: string[];
} | null;

export type TerminationProps = {
    render: TerminationRenderProps;
    callback: () => void;
};

export const Termination = ({ render, callback }: TerminationProps) => {
    if (!render) {
        return null;
    }
    return (
        <>
            {render.expired ? (
                <ExpiredLogo width="300px" />
            ) : (
                <ActiveLogo width="300px" />
            )}
            <button onClick={callback}>clickMe</button>
        </>
    );
};
