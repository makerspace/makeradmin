import React from 'react';

const Button = ({ handleClick, className, children }) => {
  return (
    <button onClick={handleClick} class={className}>
      {children}
    </button>
  );
};

export default Button;