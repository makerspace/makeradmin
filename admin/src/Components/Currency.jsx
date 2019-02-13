import React from 'react';

const Currency = (props) => {
    const formatter = new Intl.NumberFormat('sv-SE', {
        // style: 'currency',
        // currency: 'SEK',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    const value = formatter.format(props.value / 100);
    return <span>{value} {props.currency}</span>;
};


export default Currency;