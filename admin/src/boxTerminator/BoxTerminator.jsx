import React from 'react';
// import Button from '../Components/Button';
import QrCodeScanner from '../Components/QrCodeScanner';
import { showError } from '../message';

class BoxTerminator extends React.Component {

    constructor(props) {
        super(props);
        this.scanCallback = this.scanCallback.bind(this);
    }

    render() {
        return (
            <div>
                <QrCodeScanner
                    qrCodeSuccessCallback={this.scanCallback}
                />
            </div>
        );
    }

    async scanCallback(scannedString) {
        // console.dir(message);
        try {
            const scannedObject = JSON.stringify(scannedString);
            if ( !scannedObject.hasOwnPropery('member_number') ) {
                throw('Not a member memberbooth tag!')
            }

            switch (scannedObject.type) {
                case value:
                    
                    break;
            
                default:
                    break;
            }

        } catch(err) {
            showError(err);
        }
    }
}

export default BoxTerminator;
