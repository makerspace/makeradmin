import JSON5 from "json5";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

// Load the locales as json5
// Verify that all locales have the same keys and arguments
// Add override locales
// Write the locales to the file
// Write .d.ts file

const localePath = "./ts/locales";
const outputPath = "./ts/generated_locales";
const localeTypeDefinitionOutput = "./ts/locales.ts";
const defaultLocale = "en";

const locales = fs
    .readdirSync(localePath)
    .map((p) => `${localePath}/${p}`)
    .filter((p) => fs.statSync(p).isDirectory());

if (!locales.includes(`${localePath}/${defaultLocale}`)) {
    throw new Error(`Default locale ${defaultLocale} not found`);
}

const verifyLocale = (
    localeData: object,
    schema: object,
    prefix: string,
    errors: string[],
) => {
    for (const key of Object.keys(schema)) {
        if (localeData[key] === undefined) {
            errors.push(`${prefix}${key} is missing`);
        } else if (schema[key] === null) {
            if (localeData[key] !== null) {
                errors.push(
                    `Expected ${prefix}${key} to be null, like in the default locale. But found ${typeof localeData[
                        key
                    ]}`,
                );
            }
        } else if (typeof schema[key] === "object") {
            if (typeof localeData[key] !== "object") {
                errors.push(
                    `Expected ${prefix}${key} to be an object, like in the default locale. But found ${typeof localeData[
                        key
                    ]}`,
                );
                continue;
            }
            verifyLocale(
                localeData[key],
                schema[key],
                `${prefix}${key}.`,
                errors,
            );
        } else {
            if (typeof localeData[key] !== typeof schema[key]) {
                errors.push(
                    `Expected ${prefix}${key} to be of type ${typeof schema[
                        key
                    ]}, like in the default locale. But found ${typeof localeData[
                        key
                    ]}`,
                );
                continue;
            }
            if (Array.isArray(schema[key])) {
                if (!Array.isArray(localeData[key])) {
                    errors.push(
                        `Expected ${prefix}${key} to be an array, like in the default locale`,
                    );
                    continue;
                }
                if (localeData[key].length !== schema[key].length) {
                    errors.push(
                        `Expected ${prefix}${key} to have ${schema[key].length} elements, like in the default locale. But found ${localeData[key].length} elements`,
                    );
                    continue;
                }
                for (const item of localeData[key]) {
                    if (typeof item !== "string") {
                        errors.push(
                            `Expected ${prefix}${key} to be an array of strings. But found an element of type ${typeof item}`,
                        );
                        continue;
                    }
                }
            }
        }
    }
};

const i18next_plural_suffixes = [
    "_zero",
    "_one",
    "_two",
    "_few",
    "_many",
    "_other",
];

const i18nextKeys = (schema: object, prefix: string) => {
    const keys: { key: string; type: string; args: null | string[] }[] = [];
    const found = new Set<string>();
    for (let key of Object.keys(schema)) {
        if (
            typeof schema[key] === "object" &&
            !Array.isArray(schema[key]) &&
            schema[key] !== null
        ) {
            keys.push(...i18nextKeys(schema[key], `${prefix}${key}.`));
        } else {
            let args: null | Set<string> = null;
            const type =
                typeof schema[key] === "string" || schema[key] == null
                    ? "string"
                    : "string[]";

            if (typeof schema[key] === "string") {
                const matches = schema[key].matchAll(
                    /\{\{([a-zA-Z0-9_\-]+?)\}\}/g,
                );
                for (const match of matches) {
                    args = args ?? new Set<string>();
                    args.add(match[1].trim());
                }
            }

            for (const strip of i18next_plural_suffixes) {
                if (key.endsWith(strip)) {
                    key = key.slice(0, -strip.length);
                    args = args ?? new Set<string>();
                    args.add("count");
                    break;
                }
            }
            const fullKey = `${prefix}${key}`;
            if (found.has(fullKey)) {
                continue;
            }

            found.add(fullKey);
            keys.push({
                key: fullKey,
                type,
                args: args !== null ? Array.from(args) : null,
            });
        }
    }
    return keys;
};

const parseLocale = (locale: string, schema: object | null) => {
    const localeName = locale.split("/").pop();
    if (localeName === undefined) {
        throw new Error(`Could not parse locale name from ${locale}`);
    }
    const localeFiles = fs
        .readdirSync(locale)
        .map((p) => `${locale}/${p}`)
        .filter((p) => p.endsWith(".json5"));

    const merged = {};

    for (const file of localeFiles) {
        const data = fs.readFileSync(file, "utf-8");
        const json = JSON5.parse(data);
        merged[file.replace(".json5", "").split("/").pop()!] = json;
    }

    if (schema !== null) {
        const errors = [];
        verifyLocale(merged, schema, "", errors);
        for (const msg of errors) {
            console.warn(`${localeName}: ${msg}`);
        }
    }

    return {
        name: localeName,
        merged,
    };
};

const schema = parseLocale(`${localePath}/${defaultLocale}`, null).merged;
const output: { name: string; merged: object }[] = [];
for (const locale of locales) {
    output.push(parseLocale(locale, schema));
}

fs.rmSync(outputPath, { recursive: true, force: true });
fs.mkdirSync(outputPath);
const exportedLocales: [string, string][] = [];
for (const o of output) {
    const p = `${outputPath}/${o.name}.json`;
    exportedLocales.push([o.name, p]);
    fs.writeFileSync(p, JSON.stringify(o.merged, null, 4) + "\n");
}
fs.writeFileSync(
    outputPath + "/DO_NOT_EDIT.md",
    "# These files are automatically generated by the build_locales.ts script. Do not edit directly.\n",
);

const localeImports = exportedLocales
    .map(
        ([name, p]) =>
            `import ${name} from "./${path.relative(
                path.dirname(localeTypeDefinitionOutput),
                p,
            )}";`,
    )
    .join("\n");
let t = `// THIS FILE IS AUTOMATICALLY GENERATED BY THE build_locales.ts SCRIPT. DO NOT EDIT.
// This is necessary because while i18next supports typescript, it is very brittle and it has a tendency
// to cause the typescript compiler to error out because it encountered a recursion limit in its type inference.
// Pre-compiling the types like this allows us to avoid that issue, for the price of having a build step.

${localeImports}

export const LOCALE_RESOURCES = {
    ${exportedLocales.map(([name]) => `${name},`).join("\n    ")}
} as const;

export type LOCALE_SCHEMA = {
`;

let varsGlobal: string[] = [];
for (const ns of Object.keys(schema)) {
    t += `\t"${ns}": \n`;
    let vars: string[] = [];

    const groups = new Map<
        string,
        {
            key: string;
            type: string;
            args: string | null;
        }[]
    >();

    // Group overloads based on the arguments and return type.
    // If we would just list every overload individually like
    //
    // translate("a"): string
    // translate("b"): string
    // translate("c"): string
    //
    // Then typescript would not allow us to call the translate function with a union type, which is very useful when doing string interpolation
    //
    // let x: "a" | "b" = ...
    // translate(x) // Error
    //
    // But if we group them like
    //
    // translate("a" | "b" | "c"): string
    //
    // Then it is allowed
    for (const key of i18nextKeys(schema[ns], "")) {
        const argsObj =
            key.args !== null
                ? "{ " +
                  key.args.map((a) => `"${a}": string | number`).join(", ") +
                  "}"
                : null;
        const groupKey = (argsObj ?? "") + ":" + key.type;
        if (!groups.has(groupKey)) {
            groups.set(groupKey, []);
        }
        groups.get(groupKey)!.push({
            key: key.key,
            type: key.type,
            args: argsObj,
        });
    }

    for (const [groupKey, values] of groups) {
        const args = values[0].args;
        const type = values[0].type;
        const keys = values.map((o) => `"${o.key}"`).join(" | ");
        const keysGlobal = values.map((o) => `"${ns}:${o.key}"`).join(" | ");
        if (args !== null) {
            vars.push(`((key: ${keys}, args: ${args}) => ${type})`);
            varsGlobal.push(`((key: ${keysGlobal}, args: ${args}) => ${type})`);
        } else {
            vars.push(`((key: ${keys}) => ${type})`);
            varsGlobal.push(`((key: ${keysGlobal}) => ${type})`);
        }
    }
    t += vars.join(" \n\t\t& ") + "\n";
}
t += "};\n";

let t2 = "export type LOCALE_SCHEMA_GLOBAL = (\n";
t2 += varsGlobal.join(" \n\t\t& ") + "\n";
t2 += ");\n";
fs.writeFileSync(localeTypeDefinitionOutput, t + "\n" + t2);

// Invoke prettier
execSync(`npx prettier --write ${localeTypeDefinitionOutput}`);
