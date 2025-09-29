import argparse
import glob
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Any

import pyjson5

SchemaElement = str | list["SchemaElement"] | dict[str, "SchemaElement"]
SchemaType = dict[str, SchemaElement]


class LocaleError(Exception):
    pass


def verify_locale(locale_data: SchemaType, schema: SchemaType, prefix: str, errors: list[str]) -> None:
    for key in schema:
        element = schema[key]
        if key not in locale_data:
            errors.append(f"{prefix}{key} is missing")
        elif element is None:
            if locale_data[key] is not None:
                errors.append(
                    f"Expected {prefix}{key} to be null, like in the default locale. But found {type(locale_data[key]).__name__}"
                )
        elif isinstance(element, dict):
            locale_element = locale_data[key]
            if not isinstance(locale_element, dict):
                errors.append(
                    f"Expected {prefix}{key} to be an object, like in the default locale. But found {type(locale_element).__name__}"
                )
                continue
            verify_locale(locale_element, element, f"{prefix}{key}.", errors)
        else:
            if type(locale_data[key]) != type(element):
                errors.append(
                    f"Expected {prefix}{key} to be of type {type(element).__name__}, like in the default locale. But found {type(locale_data[key]).__name__}"
                )
                continue
            if isinstance(element, list):
                if not isinstance(locale_data[key], list):
                    errors.append(f"Expected {prefix}{key} to be an array, like in the default locale")
                    continue
                if len(locale_data[key]) != len(element):
                    errors.append(
                        f"Expected {prefix}{key} to have {len(element)} elements, like in the default locale. But found {len(locale_data[key])} elements"
                    )
                    continue
                for item in locale_data[key]:
                    if not isinstance(item, str):
                        errors.append(
                            f"Expected {prefix}{key} to be an array of strings. But found an element of type {type(item).__name__}"
                        )
                        continue


def override_locale(base: SchemaType, override: SchemaType, prefix: str, errors: list[str]) -> SchemaType:
    if not isinstance(override, dict):
        errors.append(f"Expected locale override to be an object, but found {type(override).__name__}")
        return base

    result: SchemaType = {}
    for key in base:
        if key in override:
            base_val = base[key]
            override_val = override[key]
            if isinstance(base_val, dict) and isinstance(override_val, dict):
                result[key] = override_locale(base_val, override_val, f"{prefix}{key}.", errors)
            else:
                result[key] = override_val
        else:
            result[key] = base[key]
    for key in override:
        if key not in base:
            errors.append(f"Key '{prefix}{key}' does not exist in the base locale, but is present in the override")
    return result


i18next_plural_suffixes = [
    "_zero",
    "_one",
    "_two",
    "_few",
    "_many",
    "_other",
]


@dataclass
class I18NextKey:
    key: str
    type: str
    args: list[str] | None


def i18next_keys(schema: SchemaType, prefix: str) -> list[I18NextKey]:
    keys = []
    found = set()
    for key in schema:
        orig_key = key
        element = schema[key]
        if isinstance(element, dict) and not isinstance(element, list) and element is not None:
            keys.extend(i18next_keys(element, f"{prefix}{key}."))
        else:
            args = None
            typ = "string" if isinstance(element, str) or element is None else "string[]"
            if isinstance(element, str):
                import re

                matches = re.findall(r"\{\{([a-zA-Z0-9_\-]+?)\}\}", element)
                if matches:
                    args = set([m.strip() for m in matches])
            for strip in i18next_plural_suffixes:
                if key.endswith(strip):
                    key = key[: -len(strip)]
                    args = args or set()
                    args.add("count")
                    break
            full_key = f"{prefix}{key}"
            if full_key in found:
                continue
            found.add(full_key)
            keys.append(
                I18NextKey(
                    key=full_key,
                    type=typ,
                    args=list(args) if args else None,
                )
            )
    return keys


@dataclass
class NamedSchema:
    name: str
    merged: SchemaType


def parse_locale(
    locale_dir: str, locale_override_dir: str | None, modules: list[str], schema: SchemaType | None
) -> NamedSchema:
    locale_name = os.path.basename(locale_dir)
    if not locale_name:
        raise LocaleError(f"Could not parse locale name from {locale_dir}")
    if not os.path.isdir(locale_dir):
        raise LocaleError(f"Locale directory '{locale_dir}' does not exist.")

    included_module_dirs = []
    for mod in modules:
        dir_path = os.path.join(locale_dir, mod)
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            raise LocaleError(f"Module directory '{dir_path}' does not exist.")
        included_module_dirs.append(dir_path)

    locale_files = []
    for dir_path in included_module_dirs:
        for f in os.listdir(dir_path):
            if f.endswith(".json5"):
                locale_files.append(os.path.join(dir_path, f))

    merged: SchemaType = {}
    for file in locale_files:
        key = os.path.splitext(os.path.basename(file))[0]
        with open(file, "r", encoding="utf-8") as fp:
            data = fp.read()
            json_obj = pyjson5.loads(data)

            if locale_override_dir is not None:
                override_file = os.path.join(locale_override_dir, os.path.relpath(file, locale_dir))
                if os.path.exists(override_file):
                    with open(override_file, "r", encoding="utf-8") as fp:
                        data = fp.read()
                        errors: list[str] = []
                        json_obj = override_locale(json_obj, pyjson5.loads(data), "", errors)
                        if errors:
                            errors_str = "".join(["\n\t" + m for m in errors])
                            raise LocaleError(f"When parsing {locale_name} override at {override_file}: {errors_str}")

            merged[key] = json_obj

    if locale_override_dir is not None:
        override_pattern = os.path.join(locale_override_dir, "*", "*.json5")
        override_files = glob.glob(override_pattern)
        locale_files_set = set(os.path.relpath(f, locale_dir) for f in locale_files)
        for override_file in override_files:
            rel_override = os.path.relpath(override_file, locale_override_dir)
            if rel_override not in locale_files_set:
                raise LocaleError(
                    f"Locale override found at '{override_file}', but there's no corresponding base locale file at {os.path.join(locale_dir, rel_override)}."
                )

    if schema is not None:
        errors = []
        verify_locale(merged, schema, "", errors)
        if errors:
            errors_str = "".join(["\n\t" + m for m in errors])
            raise LocaleError(errors_str)

    return NamedSchema(
        name=locale_name,
        merged=merged,
    )


def build_locales(
    locale_path: str,
    locale_override_path: str | None,
    output_path: str,
    locale_type_definition_output: str | None,
    default_locale: str,
    module_names: list[str],
) -> None:
    schema = parse_locale(
        os.path.join(locale_path, default_locale),
        None,
        module_names,
        None,
    ).merged

    output = []
    for d in os.listdir(locale_path):
        p = os.path.join(locale_path, d)
        if os.path.isdir(p):
            override_p = os.path.join(locale_override_path, d) if locale_override_path else None

            # First parse it without override to ensure the base loads correctly
            try:
                out = parse_locale(p, None, module_names, schema)
            except LocaleError as e:
                raise LocaleError(f"When parsing locale '{p}': {e}")

            if override_p is not None:
                try:
                    out = parse_locale(p, override_p, module_names, schema)
                except LocaleError as e:
                    raise LocaleError(f"When parsing locale override '{override_p}': {e}")

            output.append(out)
        else:
            raise LocaleError(f"Unexpected file in locale directory. Expected {p} to be a directory")

    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    else:
        # Remove files but keep directory
        for file in os.listdir(output_path):
            file_path = os.path.join(output_path, file)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)

    exported_locales = []
    for o in output:
        p = os.path.join(output_path, f"{o.name}.json")
        exported_locales.append((o.name, p))
        with open(p, "w", encoding="utf-8") as fp:
            json.dump(o.merged, fp, indent=4, ensure_ascii=False, sort_keys=True)
            fp.write("\n")
        os.chmod(p, 0o666)

    with open(os.path.join(output_path, "DO_NOT_EDIT.md"), "w", encoding="utf-8") as fp:
        fp.write("# These files are automatically generated by the build_locales.ts script. Do not edit directly.\n")

    def relative_path(from_path: str, to_path: str) -> str:
        return os.path.relpath(to_path, os.path.dirname(from_path)).replace("\\", "/")

    if locale_type_definition_output is not None:
        locale_imports = "\n".join(
            [
                f'import {name} from "./{relative_path(locale_type_definition_output, p)}";'
                for name, p in exported_locales
            ]
        )

        locale_resources = "".join([f"{name},\n    " for name, _ in exported_locales])

        t = f"""// THIS FILE IS AUTOMATICALLY GENERATED BY THE build_locales.ts SCRIPT. DO NOT EDIT.
        // This is necessary because while i18next supports typescript, it is very brittle and it has a tendency
        // to cause the typescript compiler to error out because it encountered a recursion limit in its type inference.
        // Pre-compiling the types like this allows us to avoid that issue, for the price of having a build step.

        {locale_imports}

        export const LOCALE_RESOURCES = {{
            {locale_resources}
        }} as const;

        export type LOCALE_SCHEMA = {{
        """

        vars_global = []
        for ns in schema:
            t += f'\t"{ns}": \n'
            vars = []
            groups: dict[str, list[dict[str, Any]]] = {}
            element = schema[ns]
            if not isinstance(element, dict):
                raise LocaleError(f"Expected namespace {ns} to be an object")

            for key in i18next_keys(element, ""):
                args_obj = (
                    "{ " + ", ".join([f'"{a}": string | number' for a in key.args]) + "}"
                    if key.args is not None
                    else None
                )
                group_key = (args_obj or "") + ":" + key.type
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(
                    {
                        "key": key.key,
                        "type": key.type,
                        "args": args_obj,
                    }
                )
            for group_key, values in groups.items():
                args = values[0]["args"]
                typ = values[0]["type"]
                keys = " | ".join([f'"{o["key"]}"' for o in values])
                keys_global = " | ".join([f'"{ns}:{o["key"]}"' for o in values])
                if args is not None:
                    vars.append(f"((key: {keys}, args: {args}) => {typ})")
                    vars_global.append(f"((key: {keys_global}, args: {args}) => {typ})")
                else:
                    vars.append(f"((key: {keys}) => {typ})")
                    vars_global.append(f"((key: {keys_global}) => {typ})")
            t += " \n\t\t& ".join(vars) + "\n"
        t += "};\n"

        t2 = "export type LOCALE_SCHEMA_GLOBAL = (\n"
        t2 += " \n\t\t& ".join(vars_global) + "\n"
        t2 += ");\n"

        with open(locale_type_definition_output, "w", encoding="utf-8") as fp:
            fp.write(t + "\n" + t2)

        # Optionally, you can run prettier if available
        try:
            import subprocess

            # --experimental-cli speeds things up a bit. See https://e18e.dev/blog/prettier-speed-up
            subprocess.run(
                ["npx", "prettier", "--experimental-cli", "--write", locale_type_definition_output], check=True
            )
        except Exception:
            pass

        for _, p in exported_locales:
            os.chmod(p, 0o666)
        os.chmod(locale_type_definition_output, 0o666)


if __name__ == "__main__":
    # Helper to parse CLI arguments
    parser = argparse.ArgumentParser(description="Build locales")
    parser.add_argument("--locale-path", type=str, help="Path to the locales directory", required=True)
    parser.add_argument(
        "--locale-override-path",
        type=str,
        help="Path to a partially filled in locales directory which overrides the base wherever keys are present",
    )
    parser.add_argument(
        "--output", type=str, default="./generated_locales", help="Path to output generated locales", required=True
    )
    parser.add_argument(
        "--output-ts-type-definitions",
        type=str,
        default=None,
        help="Path to output TypeScript type definitions",
    )
    parser.add_argument("--default-locale", type=str, default="en", help="Default locale name")
    parser.add_argument(
        "--modules", nargs="*", type=str, help="Space-separated list of module names to include", required=True
    )
    args = parser.parse_args()

    try:
        build_locales(
            locale_path=args.locale_path,
            locale_override_path=args.locale_override_path,
            output_path=args.output,
            locale_type_definition_output=args.output_ts_type_definitions,
            default_locale=args.default_locale,
            module_names=args.modules,
        )
    except LocaleError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
