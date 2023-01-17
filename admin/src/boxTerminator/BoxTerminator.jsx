import React from 'react';
import { Link } from "react-router-dom";
import Button from '../Components/Button';
import QrCodeScanner from '../Components/QrCodeScanner'

const handleClick = () => {
    console.log("test");
  }

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
    scanCallback(message) {
        console.dir(message)
    }
}

export default BoxTerminator;
