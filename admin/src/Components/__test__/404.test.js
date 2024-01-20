import Show404 from "../404";
import { shallow } from "enzyme";
/* eslint-env jest */
describe("404", () => {
    test("renders", () => {
        const component = shallow(<Show404 />);
        expect(component.html()).toContain("<h2>404</h2>");
    });
});
