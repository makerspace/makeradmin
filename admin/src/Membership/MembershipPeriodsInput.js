import React, { useCallback, useEffect, useRef, useState } from "react";
import CategoryPeriodsInput from "../Components/CategoryPeriodsInput";
import Icon from "../Components/icons";
import CategoryPeriods from "../Models/CategoryPeriods";
import { calculateSpanDiff, filterPeriods } from "../Models/Span";
import auth from "../auth";
import { post } from "../gateway";

function MembershipPeriodsInput({ spans, member_id }) {
    const [showHistoric, setShowHistoric] = useState(true);
    const [saveDisabled, setSaveDisabled] = useState(true);

    const categoryPeriodsListRef = useRef([
        new CategoryPeriods({ category: "labaccess" }),
        new CategoryPeriods({ category: "membership" }),
        new CategoryPeriods({ category: "special_labaccess" }),
    ]);

    const categoryPeriodsList = categoryPeriodsListRef.current;

    const canSave = useCallback(() => {
        return (
            categoryPeriodsList.every((c) => c.isValid()) &&
            categoryPeriodsList.some((c) => c.isDirty())
        );
    }, [categoryPeriodsList]);

    useEffect(() => {
        const unsubscribes = [];

        unsubscribes.push(
            spans.subscribe(({ items }) => {
                categoryPeriodsList.forEach((periods) =>
                    periods.replace(filterPeriods(items, periods.category)),
                );
            }),
        );

        categoryPeriodsList.forEach((cp) => {
            unsubscribes.push(cp.subscribe(() => setSaveDisabled(!canSave())));
        });

        return () => {
            unsubscribes.forEach((u) => u());
        };
    }, [spans, categoryPeriodsList, canSave]);

    const onSave = useCallback(() => {
        const deleteSpans = [];
        const addSpans = [];
        categoryPeriodsList.forEach((cp) => {
            cp.merge();
            calculateSpanDiff({
                items: spans.items,
                categoryPeriods: cp,
                member_id,
                deleteSpans,
                addSpans,
            });
        });

        const deleteIds = deleteSpans.map((s) => s.id).join(",");
        const timestamp = new Date().getTime().toString();
        addSpans.forEach(
            (s, i) =>
                (s.creation_reason = (
                    timestamp +
                    i +
                    " gui_edit:" +
                    auth.getUsername() +
                    " replacing:" +
                    deleteIds
                ).slice(0, 255)),
        );

        const promises = [];
        promises.push(...deleteSpans.map((s) => s.del()));
        promises.push(...addSpans.map((s) => s.save()));
        Promise.all(promises).then(() => {
            spans.fetch();

            post({
                url: `/webshop/member/${member_id}/ship_labaccess_orders`,
                headers: { "Content-Type": "application/json" },
                expectedDataStatus: "ok",
            });
        });
    }, [categoryPeriodsList, spans, member_id]);

    return (
        <form
            onSubmit={(e) => {
                e.preventDefault();
                onSave();
                return false;
            }}
        >
            <input
                id="showHistoric"
                className="uk-checkbox"
                type="checkbox"
                checked={showHistoric}
                onChange={(e) => setShowHistoric(e.target.checked)}
            />
            <label
                className="uk-form-label uk-margin-small-left"
                htmlFor="showHistoric"
            >
                Visa historiska
            </label>
            {categoryPeriodsList.map((cp) => (
                <CategoryPeriodsInput
                    key={cp.category}
                    categoryPeriods={cp}
                    showHistoric={showHistoric}
                />
            ))}
            <button
                disabled={saveDisabled}
                className="uk-button uk-button-primary uk-float-right"
            >
                <Icon icon="save" /> Spara
            </button>
        </form>
    );
}

export default MembershipPeriodsInput;
