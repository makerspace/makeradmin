import React from 'react';

const Button = ({ handleClick, className, children }) => {
  return (
    <button onClick={handleClick} className={className}>
      {children}
    </button>
  );
};

export default Button;