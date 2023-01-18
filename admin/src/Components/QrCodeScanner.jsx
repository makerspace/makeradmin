import React from 'react';
import { Html5Qrcode } from 'html5-qrcode';

class QrCodeScanner extends React.Component {
    render() {
        return(<div id="QrReader" width="600px"></div>);
    }

    componentDidMount() {
        if (!(this.props.qrCodeSuccessCallback)) {
            throw new Error("qrCodeSuccessCallback is required");
        }


        const config = {
            qrbox: { width: 300, height: 300 } 
        };

        this.html5QrCode = new Html5Qrcode(/* element id */ "QrReader");
        this.html5QrCode.start({ facingMode: { exact: "environment"}}, config, this.props.qrCodeSuccessCallback);

        
    }

    componentWillUnmount() {
        try {
            this.html5QrCode.stop()
        } catch(err) {
            console.error(`Error during qrcode unmount ${err}`);
        }
    }

}

export default QrCodeScanner;