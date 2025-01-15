import { describe, expect, it } from "@jest/globals";
import { url_join } from "../Routes";

describe("url_join", () => {
    it("should join paths correctly when part of the path ends with a slash", () => {
        const paths = ["path/to/", "resource"];
        const result = url_join(paths);
        expect(result).toBe("path/to/resource");
    });

    it("should join paths correctly when no part of the path ends with a slash", () => {
        const paths = ["path/to", "resource"];
        const result = url_join(paths);
        expect(result).toBe("path/to/resource");
    });

    it("should join paths correctly when all parts of the path end with a slash", () => {
        const paths = ["path/to/", "resource/"];
        const result = url_join(paths);
        expect(result).toBe("path/to/resource");
    });
});
