/// This file contains a bunch of hard to understand typescript types.
/// They are used to type check the translation dictionary.
/// The dictionary is a nested object with string keys and string/function values.
///
/// This file should rarely require any modifications.
///
/// See https://stackoverflow.com/questions/58277973/how-to-type-check-i18n-dictionaries-with-typescript

import { VNode, isValidElement } from "preact";

// T is the dictionary, S ist the next string part of the object property path
// If S does not match dict shape, return its next expected properties 
type DeepKeys<T, S extends string> =
T extends VNode ? "" :
(T extends object
? S extends `${infer I1}.${infer I2}`
    ? I1 extends keyof T
        // fix issue allowed last dot
        ? T[I1] extends object
            ? `${I1}.${DeepKeys<T[I1], I2>}`
            : keyof T & string
        : keyof T & string
    : S extends keyof T
        ? `${S}`
        : keyof T & string
: "");


/// Get all possible key paths
type DeepKeysAll<T> = T extends VNode ? "" : (T extends object ? {
    [K in keyof T]-?: `${K & string}` | Concat<K & string, DeepKeysAll<T[K]>>
}[keyof T] : "");

type Concat<K extends string, P extends string> =
    `${K}${"" extends P ? "" : "."}${P}`;

// or: only get leaf and no intermediate key path
export type TranslationKeyValues<T> = T extends object ?
    { [K in keyof T]-?: Concat<K & string, DeepKeysAll<T[K]>> }[keyof T] : "";

/// Returns property value from object O given property path T, otherwise never
type GetDictValue<T extends string, O> =
    T extends `${infer A}.${infer B}` ? 
    A extends keyof O ? GetDictValue<B, O[A]> : never
    : T extends keyof O ? O[T] : never;


export class Translation<T extends Record<string, any>> {
    translations: T;

    constructor(translations: T) {
        this.translations = translations;
    }

    /// Get translation value for key
    t<S extends string>(key: DeepKeys<T, S>): GetDictValue<S, T> {
        const parts = key.split(".");
        let item = this.translations as Record<string, any>;
        for (let i = 0; i < parts.length - 1; i++) {
            let child = item[parts[i]];
            if (child === null || child === undefined) {
                throw new Error("Missing translation for " + key);
            } else if (typeof child !== "object") {
                throw new Error("Missing translation for " + key);
            }
            item = child;
        }
        const v = item[parts[parts.length-1]];
        if (typeof v !== "object" || Array.isArray(v) || isValidElement(v)) {
            return v as unknown as GetDictValue<S, T>;
        } else {
            throw new Error("Missing translation for " + key + ". " + v);
        }
    }
}
