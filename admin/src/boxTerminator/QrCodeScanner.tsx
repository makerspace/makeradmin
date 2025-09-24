import type * as module_type from "html5-qrcode";
import { FC, useEffect, useState } from "react";

type QrCodeScannerProps = {
    onSuccess: (qrCodeMessage: string) => void;
};

const allowedErrors = [
    'NotFoundException',
    "error = D:",
];

const QrCodeScanner: FC<QrCodeScannerProps> = ({ onSuccess }) => {
    const [module, setModule] = useState<typeof module_type | null>(null);

    useEffect(() => {
        import("html5-qrcode").then((module) => setModule(module));
    }, []);

    useEffect(() => {
        if (module === null) return;

        const scanner = new module.Html5Qrcode("qr-reader", {
            formatsToSupport: [module.Html5QrcodeSupportedFormats.QR_CODE],
            verbose: false,
        });

        const qrboxFunction = function (
            viewfinderWidth: number,
            viewfinderHeight: number,
        ) {
            let minEdgePercentage = 0.85;
            let minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
            let qrboxSize = Math.floor(minEdgeSize * minEdgePercentage);
            return {
                width: qrboxSize,
                height: qrboxSize,
            };
        };

        scanner.start(
            { facingMode: "environment" }, // Prefer rear camera on mobiles
            {
                fps: 15,
                qrbox: qrboxFunction,
            },
            (qrCodeMessage) => onSuccess(qrCodeMessage),
            (errorMessage) => {

                if (allowedErrors.some((error) => errorMessage.includes(error))) return;

                console.error(errorMessage);
            },
        );

        return () => {
            if (scanner.isScanning) {
                scanner.stop().then(() => {
                    scanner.clear();
                });
            } else {
                scanner.clear();
            }
        };
    }, [module]);

    return <div id="qr-reader" />;
};

export default QrCodeScanner;
