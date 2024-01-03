import React, { useState } from "react";
// import Button from '../Components/Button';
import QrCodeScanner from "./QrCodeScanner";
import { showError } from "../message";
import { get } from "../gateway";
import { Termination, TerminationRenderProps } from "./Termination";

type ResponseType = TerminationRenderProps;

const BoxTerminator = () => {
    const [runScanner, setRunScanner] = useState(true);
    const [response, setResponse] = useState(null as ResponseType);
    const scanCallback = (scannedString: string) => {
        try {
            get({
                url: `/box_terminator/fetch/${scannedString}`,
                // data: { message: scannedString },
            }).then((res) => {
                if (res.status === "ok") {
                    // alert("Box terminated successfully!");
                    setResponse(JSON.parse(res.data));
                    setRunScanner(false);
                }
            });
        } catch (err) {
            showError(err);
        }
    };
    return (
        <div
            style={{
                textAlign: "center",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
            }}
        >
            {runScanner ? (
                <QrCodeScanner
                    onSuccess={scanCallback}
                    filterScan={(scannedString) => {
                        const parsedString = JSON.parse(scannedString);
                        if (!parsedString.hasOwnProperty("member_number")) {
                            showError("Not a member memberbooth tag!");
                            return false;
                        }
                        return true;
                    }}
                />
            ) : (
                <>
                    <Termination
                        render={response}
                        callback={() => setRunScanner(true)}
                    />
                </>
            )}
        </div>
    );
};

export default BoxTerminator;
