/* eslint-env jest */

import React from 'react';
import {shallow} from "enzyme";
import Show404 from "../404";

describe("404", () => {
    
    test("renders", () => {
        const component = shallow(<Show404/>);
        expect(component.html()).toContain("<h2>404</h2>");
    });
});

