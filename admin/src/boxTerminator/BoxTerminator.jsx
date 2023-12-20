import React from 'react';
// import Button from '../Components/Button';
import QrCodeScanner from '../Components/QrCodeScanner';
import { showError } from '../message';

class BoxTerminator extends React.Component {

    constructor(props) {
        super(props);
        this.scanCallback = this.scanCallback.bind(this);
    }

    scanCallback(scannedString) {
        // console.dir(message);
        try {
            const scannedObject = JSON.stringify(scannedString);
            console.dir(scannedObject)
            if ( !scannedObject.hasOwnPropery('member_number') ) {
                throw(new Error('Not a member memberbooth tag!'));
            }

            switch (scannedObject.type) {
                case "":
                    
                    break;
            
                default:
                    break;
            }

        } catch(err) {
            showError(err);
        }
    }
    render() {
        return (
            <div>
                <QrCodeScanner onSuccess={this.scanCallback} filterScan={(ignore) => {return true}}/>
            </div>
        );
    }
}

export default BoxTerminator;
