import React, {useEffect } from "react";
import { Html5Qrcode, Html5QrcodeSupportedFormats } from "html5-qrcode";

const QrCodeScanner = ({ filterScan, onSuccess }) => {
  useEffect(() => {
    const scanner = new Html5Qrcode("qr-reader", {
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
    });

    scanner.start(
      { facingMode: "environment" }, // Prefer rear camera on mobiles
      {
        fps: 15,
        qrbox: 300,
      },
      (qrCodeMessage) => {
        if (filterScan(qrCodeMessage)) {
          scanner.stop().then(() => {
            // QR Code scanning is stopped.
            onSuccess(qrCodeMessage);
          });
        }
      }
    );

    return () => {
      scanner.clear();
    };
  }, []);

  return <div id="qr-reader" style={{ width: "100%", height: "100%" }} />;
};

export default QrCodeScanner;